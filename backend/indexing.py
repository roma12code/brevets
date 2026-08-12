# indexing.py
# Indexation universelle des 3 types de documents MedTech dans ChromaDB

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import json
import os

# ══════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════

CHUNKS_FILE = "4_Chunks/MASTER_chunks.json"   # ⭐ Le master fichier de chunking.py
COLLECTION_NAME = "medtech_collection"         # Une seule collection pour les 3 types
DB_PATH = "./5_ChromaDB"                       # Dossier où ChromaDB stocke les vecteurs
MODEL_NAME = "BAAI/bge-large-en-v1.5"          # Même modèle que ton ancien code
BATCH_SIZE = 32   #2^5                         # Taille des lots


# ══════════════════════════════════════════════════════
# FONCTION 1 : Charger les chunks depuis le JSON
# ══════════════════════════════════════════════════════

def load_chunks(chunks_file):
    """Charge le fichier JSON des chunks"""
    print(f"📂 Chargement des chunks depuis {chunks_file}...")
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"   ✅ {len(chunks)} chunks chargés")
    
    # Statistiques par type
    from collections import Counter
    types_count = Counter([c['metadata']['type_document'] for c in chunks])
    print("\n📊 Répartition :")
    for doc_type, count in types_count.items():
        print(f"   • {doc_type} : {count} chunks")
    
    return chunks


# ══════════════════════════════════════════════════════
# FONCTION 2 : Nettoyer les métadonnées pour ChromaDB
# ══════════════════════════════════════════════════════

def clean_metadata(metadata):
    """
    ChromaDB n'accepte que str, int, float, bool dans les métadonnées.
    On nettoie pour éviter les erreurs.
    """
    cleaned = {}
    for key, value in metadata.items():
        if value is None or value == 'nan':
            cleaned[key] = ""
        elif isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned


# ══════════════════════════════════════════════════════
# FONCTION 3 : Indexer les chunks dans ChromaDB
# ══════════════════════════════════════════════════════

def indexer(chunks, collection_name=COLLECTION_NAME, db_path=DB_PATH):
    """
    Indexe tous les chunks (Brevets + Certificats + Modèles) dans ChromaDB.
    """
    
    print("\n" + "=" * 60)
    print("   🧠 INDEXATION DANS CHROMADB")
    print("=" * 60)
    
    # ─── Étape 1 : Charger le modèle d'embedding ───
    print(f"\n🤖 Chargement du modèle : {MODEL_NAME}")
    print("   (Premier téléchargement ~1.3 GB, ensuite c'est rapide)")
    model = SentenceTransformer(MODEL_NAME)
    print("   ✅ Modèle chargé")
    
    # ─── Étape 2 : Initialiser ChromaDB ───
    print(f"\n🗄️ Initialisation de ChromaDB dans : {db_path}")
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)
    
    # Supprimer l'ancienne collection si elle existe
    try:
        client.delete_collection(name=collection_name)
        print(f"   🗑️ Ancienne collection '{collection_name}' supprimée")
    except:
        print(f"   ℹ️ Pas d'ancienne collection à supprimer")
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # Cosine similarity (meilleur pour le texte)
    )
    print(f"   ✅ Nouvelle collection '{collection_name}' créée")
    
    # ─── Étape 3 : Indexer par batchs ───
    print(f"\n⚙️ Indexation de {len(chunks)} chunks (par lots de {BATCH_SIZE})...")
    print("   ⏳ Cela peut prendre 10-30 minutes selon ton PC...\n")
    
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="🔄 Indexation"):
        batch = chunks[i:i + BATCH_SIZE]
        
        # Extraire les données
        texts = [chunk['text'] for chunk in batch]
        ids = [chunk['chunk_id'] for chunk in batch]
        metadatas = [clean_metadata(chunk['metadata']) for chunk in batch]
        
        # Générer les embeddings
        embeddings = model.encode(
            texts, 
            show_progress_bar=False, 
            normalize_embeddings=True
        ).tolist()
        
        # Ajouter à ChromaDB
        collection.add(
            embeddings=embeddings,
            documents=texts,
            ids=ids,
            metadatas=metadatas
        )
    
    # ─── Étape 4 : Vérification finale ───
    total_indexed = collection.count()
    
    print("\n" + "=" * 60)
    print("   ✅ INDEXATION TERMINÉE !")
    print("=" * 60)
    print(f"📦 Collection : {collection_name}")
    print(f"📊 Total chunks indexés : {total_indexed}")
    print(f"💾 Base sauvegardée : {os.path.abspath(db_path)}")
    
    return collection


# ══════════════════════════════════════════════════════
# FONCTION 4 : Test rapide de recherche
# ══════════════════════════════════════════════════════

def test_search(collection, model, query="cardiac monitoring device", n_results=3):
    """Test rapide pour vérifier que l'indexation fonctionne"""
    
    print("\n" + "=" * 60)
    print("   🔍 TEST DE RECHERCHE")
    print("=" * 60)
    print(f"❓ Question : '{query}'\n")
    
    # Générer l'embedding de la question
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()
    
    # Rechercher dans ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    # Afficher les résultats
    for i, (doc, meta, distance) in enumerate(zip(
        results['documents'][0], 
        results['metadatas'][0],
        results['distances'][0]
    )):
        similarity = (1 - distance) * 100  # Convertir distance en %
        print(f"📄 Résultat {i+1} (Similarité : {similarity:.1f}%)")
        print(f"   Type : {meta.get('type_document', 'N/A')}")
        print(f"   Titre : {meta.get('title', 'N/A')[:80]}...")
        print(f"   Texte : {doc[:150]}...")
        print()


# ══════════════════════════════════════════════════════
# FONCTION 5 : Test avec filtre par type
# ══════════════════════════════════════════════════════

def test_search_with_filter(collection, model, query="medical implant", doc_type="Brevet d'invention", n_results=3):
    """Test de recherche FILTREE par type de document"""
    
    print("\n" + "=" * 60)
    print(f"   🎯 RECHERCHE FILTRÉE : {doc_type}")
    print("=" * 60)
    print(f"❓ Question : '{query}'\n")
    
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()
    
    # ⭐ Recherche AVEC filtre sur type_document
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where={"type_document": doc_type}  # Filtre magique !
    )
    
    for i, (doc, meta, distance) in enumerate(zip(
        results['documents'][0], 
        results['metadatas'][0],
        results['distances'][0]
    )):
        similarity = (1 - distance) * 100
        print(f"📄 Résultat {i+1} (Similarité : {similarity:.1f}%)")
        print(f"   Type : {meta.get('type_document', 'N/A')}")
        print(f"   Titre : {meta.get('title', 'N/A')[:80]}...")
        print()


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    
    print("🚀 PIPELINE D'INDEXATION MEDTECH")
    print("=" * 60)
    
    # 1. Charger les chunks
    chunks = load_chunks(CHUNKS_FILE)
    
    # 2. Indexer dans ChromaDB
    collection = indexer(chunks)
    
    # 3. Tests
    print("\n\n🧪 LANCEMENT DES TESTS DE VÉRIFICATION...")
    
    model = SentenceTransformer(MODEL_NAME)
    
    # Test 1 : Recherche globale (tous types)
    test_search(collection, model, query="cardiac pacemaker", n_results=3)
    
    # Test 2 : Recherche filtrée par type
    test_search_with_filter(collection, model, 
                           query="surgical robot", 
                           doc_type="Brevet d'invention", 
                           n_results=3)
    
    test_search_with_filter(collection, model, 
                           query="medical device design", 
                           doc_type="Modèle industriel", 
                           n_results=3)
    
    
    print("   PIPELINE COMPLET TERMINÉ !")
    print("\n💡 Prochaine étape : Création de l'Agent IA avec RAG !")
