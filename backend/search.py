# search.py
# Recherche universelle dans ChromaDB pour Brevets, Certificats et Modèles Industriels

import chromadb
from sentence_transformers import SentenceTransformer

# ══════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════

COLLECTION_NAME = "medtech_collection"   # ⭐ Nouvelle collection unifiée
DB_PATH = "./5_ChromaDB"
MODEL_NAME = "BAAI/bge-large-en-v1.5"

# Variables globales (cache pour éviter de recharger à chaque fois)
_model = None
_collection = None


# ══════════════════════════════════════════════════════
# FONCTION 1 : Initialisation
# ══════════════════════════════════════════════════════

def init_search(collection_name=COLLECTION_NAME, db_path=DB_PATH):
    """Initialise le modèle et la collection ChromaDB"""
    global _model, _collection
    
    if _model is None:
        print("🤖 Chargement du modèle BGE...")
        _model = SentenceTransformer(MODEL_NAME)
        print("   ✅ Modèle prêt")
    
    if _collection is None:
        print("🗄️ Connexion à ChromaDB...")
        client = chromadb.PersistentClient(path=db_path)
        try:
            _collection = client.get_collection(name=collection_name)
            print(f"   ✅ Collection '{collection_name}' chargée ({_collection.count()} chunks)")
        except Exception as e:
            raise ValueError(
                f"❌ La collection '{collection_name}' n'existe pas.\n"
                f"   Lance d'abord l'indexation avec: python indexing.py\n"
                f"   Erreur : {e}"
            )
    
    return _model, _collection


# ══════════════════════════════════════════════════════
# FONCTION 2 : Recherche UNIVERSELLE (les 3 types)
# ══════════════════════════════════════════════════════

def rechercher_documents(question, n_resultats=5, filtre_type=None, filtre_year=None, filtre_assignee=None):
    """
    Recherche les documents les plus pertinents dans les 3 types.
    
    Args:
        question (str): La question de l'utilisateur
        n_resultats (int): Nombre de résultats à retourner
        filtre_type (str): "Brevet d'invention", "Certificat d'utilité", "Modèle industriel" ou None
        filtre_year (str): Année spécifique (ex: "2023") ou None
        filtre_assignee (str): Entreprise spécifique (ex: "Medtronic") ou None
    
    Returns:
        list: Liste de documents trouvés avec leurs métadonnées
    """
    model, collection = init_search()
    
    # Encoder la question en vecteur
    vecteur_question = model.encode(question, normalize_embeddings=True).tolist()
    
    # ⭐ CONSTRUIRE LES FILTRES (très important pour la précision !)
    where_filter = build_filters(filtre_type, filtre_year, filtre_assignee)
    
    # Recherche dans ChromaDB
    resultats = collection.query(
        query_embeddings=[vecteur_question],
        n_results=n_resultats,
        where=where_filter,
        include=['documents', 'metadatas', 'distances']
    )
    
    # Formater les résultats
    documents_trouves = []
    for i in range(len(resultats['documents'][0])):
        meta = resultats['metadatas'][0][i]
        
        document = {
            'texte': resultats['documents'][0][i],
            'titre': meta.get('title', ''),
            'type_document': meta.get('type_document', ''),     # ⭐ Nouveau
            'id': meta.get('id', ''),
            'assignee': meta.get('assignee', ''),
            'cpc': meta.get('cpc', ''),
            'year': meta.get('year', ''),
            'inventor': meta.get('inventor', ''),               # ⭐ Nouveau
            'similarite': round(1 - resultats['distances'][0][i], 4),
            'distance': round(resultats['distances'][0][i], 4)
        }
        documents_trouves.append(document)
    
    return documents_trouves


# ══════════════════════════════════════════════════════
# FONCTION 3 : Construire les filtres (logique ChromaDB)
# ══════════════════════════════════════════════════════

def build_filters(filtre_type=None, filtre_year=None, filtre_assignee=None):
    """
    Construit le dictionnaire de filtres pour ChromaDB.
    ChromaDB utilise une syntaxe spéciale avec $and, $eq, etc.
    """
    filters = []
    
    if filtre_type:
        filters.append({"type_document": {"$eq": filtre_type}})
    
    if filtre_year:
        filters.append({"year": {"$eq": str(filtre_year)}})
    
    if filtre_assignee:
        filters.append({"assignee": {"$eq": filtre_assignee}})
    
    # Aucun filtre
    if len(filters) == 0:
        return None
    
    # Un seul filtre
    if len(filters) == 1:
        return filters[0]
    
    # Plusieurs filtres : utilise $and
    return {"$and": filters}


# ══════════════════════════════════════════════════════
# FONCTION 4 : Recherche par type spécifique (raccourcis)
# ══════════════════════════════════════════════════════

def rechercher_brevets(question, n_resultats=5, filtre_year=None):
    """Raccourci : Recherche UNIQUEMENT dans les brevets d'invention"""
    return rechercher_documents(
        question, 
        n_resultats=n_resultats, 
        filtre_type="Brevet d'invention",
        filtre_year=filtre_year
    )


def rechercher_certificats(question, n_resultats=5, filtre_year=None):
    """Raccourci : Recherche UNIQUEMENT dans les certificats d'utilité"""
    return rechercher_documents(
        question, 
        n_resultats=n_resultats, 
        filtre_type="Certificat d'utilité",
        filtre_year=filtre_year
    )


def rechercher_modeles(question, n_resultats=5, filtre_year=None):
    """Raccourci : Recherche UNIQUEMENT dans les modèles industriels"""
    return rechercher_documents(
        question, 
        n_resultats=n_resultats, 
        filtre_type="Modèle industriel",
        filtre_year=filtre_year
    )


# ══════════════════════════════════════════════════════
# FONCTION 5 : Statistiques de la base
# ══════════════════════════════════════════════════════

def get_statistics():
    """Retourne des statistiques sur la base de données"""
    _, collection = init_search()
    
    total = collection.count()
    
    # Compter par type
    types_count = {}
    for doc_type in ["Brevet d'invention", "Certificat d'utilité", "Modèle industriel"]:
        try:
            results = collection.get(
                where={"type_document": doc_type},
                limit=1  # On veut juste le compte, pas les données
            )
            # Méthode pour compter avec filtre
            count_results = collection.get(
                where={"type_document": doc_type}
            )
            types_count[doc_type] = len(count_results['ids'])
        except Exception as e:
            types_count[doc_type] = 0
    
    return {
        'total_chunks': total,
        'repartition': types_count
    }


# ══════════════════════════════════════════════════════
# TESTS (à exécuter avec: python search.py)
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("   🧪 TESTS DU MOTEUR DE RECHERCHE")
    print("=" * 60)
    
    # Test 1 : Statistiques de la base
    print("\n📊 STATISTIQUES DE LA BASE")
    print("-" * 60)
    stats = get_statistics()
    print(f"Total chunks : {stats['total_chunks']}")
    print("Répartition :")
    for doc_type, count in stats['repartition'].items():
        print(f"   • {doc_type} : {count}")
    
    # Test 2 : Recherche globale (tous types)
    print("\n\n🔍 TEST 1 : Recherche globale")
    print("-" * 60)
    question = "cardiac pacemaker for heart monitoring"
    print(f"❓ Question : '{question}'\n")
    
    results = rechercher_documents(question, n_resultats=3)
    for i, doc in enumerate(results, 1):
        print(f"📄 Résultat {i} (Similarité : {doc['similarite']*100:.1f}%)")
        print(f"   Type    : {doc['type_document']}")
        print(f"   Titre   : {doc['titre'][:80]}")
        print(f"   Société : {doc['assignee']}")
        print(f"   Année   : {doc['year']}")
        print()
    
    # Test 3 : Recherche filtrée - Brevets uniquement
    print("\n🔍 TEST 2 : Brevets uniquement")
    print("-" * 60)
    question = "surgical robot for minimally invasive surgery"
    print(f"❓ Question : '{question}' (Brevets uniquement)\n")
    
    results = rechercher_brevets(question, n_resultats=3)
    for i, doc in enumerate(results, 1):
        print(f"📄 Résultat {i} (Similarité : {doc['similarite']*100:.1f}%)")
        print(f"   Type    : {doc['type_document']}")
        print(f"   Titre   : {doc['titre'][:80]}")
        print()
    
    # Test 4 : Recherche filtrée - Modèles industriels uniquement
    print("\n🔍 TEST 3 : Modèles industriels uniquement")
    print("-" * 60)
    question = "medical device design"
    print(f"❓ Question : '{question}' (Modèles industriels uniquement)\n")
    
    results = rechercher_modeles(question, n_resultats=3)
    for i, doc in enumerate(results, 1):
        print(f"📄 Résultat {i} (Similarité : {doc['similarite']*100:.1f}%)")
        print(f"   Type    : {doc['type_document']}")
        print(f"   Titre   : {doc['titre'][:80]}")
        print()
    
    # Test 5 : Recherche avec multi-filtres
    print("\n🔍 TEST 4 : Multi-filtres (Brevets + 2023)")
    print("-" * 60)
    question = "medical imaging"
    print(f"❓ Question : '{question}' (Brevets de 2023)\n")
    
    results = rechercher_documents(
        question, 
        n_resultats=3,
        filtre_type="Brevet d'invention",
        filtre_year="2023"
    )
    for i, doc in enumerate(results, 1):
        print(f"📄 Résultat {i} (Similarité : {doc['similarite']*100:.1f}%)")
        print(f"   Type    : {doc['type_document']}")
        print(f"   Titre   : {doc['titre'][:80]}")
        print(f"   Année   : {doc['year']}")
        print()
    
    print("\n" + "🎉" * 30)
    print("   TESTS TERMINÉS !")
    print("🎉" * 30)
