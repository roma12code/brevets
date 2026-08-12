# rag_pipeline.py
# Pipeline RAG pour l'analyse d'antériorité (Prior Art Search) MedTech

from search import rechercher_documents, get_statistics
from datetime import datetime

# ══════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════

# Seuils de similarité pour décider si une idée existe déjà
SEUIL_SIMILARITE_HAUTE = 0.75    # > 75% = idée très similaire (existe probablement)
SEUIL_SIMILARITE_MOYENNE = 0.60  # 60-75% = idée partiellement existante
SEUIL_SIMILARITE_BASSE = 0.45    # 45-60% = idée légèrement liée

NB_RESULTATS_ANALYSE = 10        # On récupère 10 documents pour analyse


# ══════════════════════════════════════════════════════
# FONCTION 1 : Analyser une idée d'invention
# ══════════════════════════════════════════════════════

def analyser_idee_invention(idee, type_document=None, verbose=True):
    """
    Analyse une idée d'invention et détermine si elle existe déjà.
    
    Args:
        idee (str): Description de l'invention proposée
        type_document (str): Filtre par type (optionnel)
        verbose (bool): Afficher les détails
    
    Returns:
        dict: Analyse complète avec recommandations
    """
    
    if verbose:
        print("\n" + "=" * 70)
        print("   🔬 ANALYSE D'ANTÉRIORITÉ - PRIOR ART SEARCH")
        print("=" * 70)
        print(f"\n💡 Idée à analyser :\n   '{idee[:150]}...'\n")
    
    # ─── Étape 1 : Recherche dans la base ───
    if verbose:
        print("🔍 Étape 1 : Recherche dans la base de 23 462 documents...")
    
    documents_similaires = rechercher_documents(
        question=idee,
        n_resultats=NB_RESULTATS_ANALYSE,
        filtre_type=type_document
    )
    
    if verbose:
        print(f"   ✅ {len(documents_similaires)} documents pertinents trouvés\n")
    
    # ─── Étape 2 : Analyse statistique des résultats ───
    analyse = analyser_resultats(documents_similaires)
    
    # ─── Étape 3 : Décision automatique ───
    decision = prendre_decision(analyse, documents_similaires)
    
    # ─── Étape 4 : Préparer le contexte pour le LLM ───
    contexte_llm = preparer_contexte_llm(idee, documents_similaires, decision)
    
    # ─── Résultat final ───
    resultat = {
        'idee_originale': idee,
        'date_analyse': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'nb_documents_analyses': len(documents_similaires),
        'documents_similaires': documents_similaires,
        'analyse_statistique': analyse,
        'decision': decision,
        'contexte_pour_llm': contexte_llm
    }
    
    if verbose:
        afficher_resultat(resultat)
    
    return resultat


# ══════════════════════════════════════════════════════
# FONCTION 2 : Analyse statistique des résultats
# ══════════════════════════════════════════════════════

def analyser_resultats(documents):
    """Analyse les statistiques des documents trouvés"""
    
    if not documents:
        return {
            'similarite_max': 0,
            'similarite_moyenne': 0,
            'nb_haute_similarite': 0,
            'nb_moyenne_similarite': 0,
            'nb_basse_similarite': 0,
            'types_documents': {},
            'entreprises_top': {},
            'annees_distribution': {}
        }
    
    # Similarités
    similarites = [doc['similarite'] for doc in documents]
    
    # Compter par catégorie de similarité
    nb_haute = sum(1 for s in similarites if s >= SEUIL_SIMILARITE_HAUTE)
    nb_moyenne = sum(1 for s in similarites if SEUIL_SIMILARITE_MOYENNE <= s < SEUIL_SIMILARITE_HAUTE)
    nb_basse = sum(1 for s in similarites if SEUIL_SIMILARITE_BASSE <= s < SEUIL_SIMILARITE_MOYENNE)
    
    # Types de documents
    types = {}
    for doc in documents:
        t = doc.get('type_document', 'Inconnu')
        types[t] = types.get(t, 0) + 1
    
    # Top entreprises
    entreprises = {}
    for doc in documents:
        e = doc.get('assignee', 'Inconnu')
        if e and e != 'Inconnu':
            entreprises[e] = entreprises.get(e, 0) + 1
    
    # Distribution par année
    annees = {}
    for doc in documents:
        a = doc.get('year', 'Inconnu')
        if a:
            annees[a] = annees.get(a, 0) + 1
    
    return {
        'similarite_max': max(similarites),
        'similarite_moyenne': sum(similarites) / len(similarites),
        'nb_haute_similarite': nb_haute,
        'nb_moyenne_similarite': nb_moyenne,
        'nb_basse_similarite': nb_basse,
        'types_documents': types,
        'entreprises_top': dict(sorted(entreprises.items(), key=lambda x: x[1], reverse=True)[:5]),
        'annees_distribution': dict(sorted(annees.items(), reverse=True))
    }


# ══════════════════════════════════════════════════════
# FONCTION 3 : Prendre une décision automatique
# ══════════════════════════════════════════════════════

def prendre_decision(analyse, documents):
    """
    Décide si l'idée existe déjà ou pas selon les similarités trouvées.
    
    Returns:
        dict: Décision avec verdict et explication
    """
    
    sim_max = analyse['similarite_max']
    nb_haute = analyse['nb_haute_similarite']
    nb_moyenne = analyse['nb_moyenne_similarite']
    
    # CAS 1 : Idée DÉJÀ EXISTANTE (haute similarité)
    if sim_max >= SEUIL_SIMILARITE_HAUTE and nb_haute >= 2:
        return {
            'verdict': 'IDEE_EXISTANTE',
            'niveau_risque': 'ÉLEVÉ',
            'emoji': '❌',
            'titre': "Idée probablement déjà brevetée",
            'explication': f"Nous avons trouvé {nb_haute} documents très similaires (>{SEUIL_SIMILARITE_HAUTE*100:.0f}% de similarité). Votre idée est probablement déjà couverte par des brevets existants.",
            'recommandation': "Examinez attentivement les brevets similaires ci-dessous. Vous devrez prouver une innovation significative pour breveter votre idée."
        }
    
    # CAS 2 : Idée PARTIELLEMENT existante
    elif sim_max >= SEUIL_SIMILARITE_MOYENNE or nb_moyenne >= 3:
        return {
            'verdict': 'IDEE_PARTIELLEMENT_EXISTANTE',
            'niveau_risque': 'MOYEN',
            'emoji': '⚠️',
            'titre': "Idée partiellement couverte",
            'explication': f"Similarité maximale : {sim_max*100:.1f}%. Quelques brevets touchent à votre domaine sans être identiques.",
            'recommandation': "Différenciez clairement votre invention des brevets existants. Concentrez-vous sur les aspects innovants."
        }
    
    # CAS 3 : Idée NOUVELLE
    else:
        return {
            'verdict': 'IDEE_NOUVELLE',
            'niveau_risque': 'FAIBLE',
            'emoji': '✅',
            'titre': "Idée potentiellement brevetable !",
            'explication': f"Aucun document fortement similaire trouvé (max : {sim_max*100:.1f}%). Votre idée semble nouvelle dans notre base.",
            'recommandation': "Procédez à une analyse approfondie. Considérez une recherche d'antériorité plus large avant de déposer."
        }


# ══════════════════════════════════════════════════════
# FONCTION 4 : Préparer le contexte pour le LLM
# ══════════════════════════════════════════════════════

def preparer_contexte_llm(idee, documents, decision):
    """
    Prépare un prompt structuré pour envoyer au LLM (Groq + Llama 3.3)
    """
    
    # Construire le contexte des documents similaires
    contexte_docs = ""
    for i, doc in enumerate(documents[:5], 1):  # Top 5 pour le LLM
        contexte_docs += f"""
DOCUMENT {i} :
- Type : {doc.get('type_document', 'N/A')}
- Titre : {doc.get('titre', 'N/A')}
- Entreprise : {doc.get('assignee', 'N/A')}
- Année : {doc.get('year', 'N/A')}
- Similarité : {doc['similarite']*100:.1f}%
- Extrait : {doc['texte'][:400]}...
---
"""
    
    # Construire le prompt pour le LLM
    prompt = f"""Tu es un expert en propriété intellectuelle spécialisé dans le domaine MedTech (technologies médicales).

MISSION : Analyser l'idée d'invention suivante et fournir une analyse experte.

IDÉE D'INVENTION PROPOSÉE :
{idee}

VERDICT AUTOMATIQUE PRÉLIMINAIRE :
{decision['emoji']} {decision['titre']}
- Niveau de risque : {decision['niveau_risque']}
- {decision['explication']}

DOCUMENTS SIMILAIRES TROUVÉS DANS LA BASE (Top 5) :
{contexte_docs}

INSTRUCTIONS :
Fournis une analyse structurée en français avec les sections suivantes :

1. 🔍 **ANALYSE D'ANTÉRIORITÉ**
   - L'idée existe-t-elle déjà ? Justifier.
   - Quels brevets similaires sont les plus pertinents ?

2. 💡 **DIFFÉRENCIATION POSSIBLE** (si applicable)
   - Comment l'inventeur peut-il différencier son idée ?
   - Quels aspects innovants pourraient être protégés ?

3. ⚖️ **ANALYSE DE BREVETABILITÉ**
   - Nouveauté : L'idée est-elle nouvelle ?
   - Activité inventive : Est-elle non-évidente ?
   - Application industrielle : Est-elle applicable ?

4. 🎯 **RECOMMANDATIONS STRATÉGIQUES**
   - Faut-il continuer le développement ?
   - Quelles classifications CPC suggérer ?
   - Quels concurrents surveiller ?

5. 📋 **CONCLUSION**
   - Verdict final
   - Prochaines étapes recommandées

Sois précis, professionnel et utilise les données fournies."""
    
    return prompt


# ══════════════════════════════════════════════════════
# FONCTION 5 : Afficher le résultat
# ══════════════════════════════════════════════════════

def afficher_resultat(resultat):
    """Affiche joliment le résultat de l'analyse"""
    
    print("\n" + "=" * 70)
    print("   📊 RÉSULTAT DE L'ANALYSE")
    print("=" * 70)
    
    # Décision
    d = resultat['decision']
    print(f"\n{d['emoji']} VERDICT : {d['titre']}")
    print(f"   Niveau de risque : {d['niveau_risque']}")
    print(f"   {d['explication']}")
    print(f"\n💡 Recommandation : {d['recommandation']}")
    
    # Statistiques
    a = resultat['analyse_statistique']
    print(f"\n📈 STATISTIQUES DES {resultat['nb_documents_analyses']} DOCUMENTS ANALYSÉS :")
    print(f"   • Similarité maximale : {a['similarite_max']*100:.1f}%")
    print(f"   • Similarité moyenne  : {a['similarite_moyenne']*100:.1f}%")
    print(f"   • Très similaires (>{SEUIL_SIMILARITE_HAUTE*100:.0f}%) : {a['nb_haute_similarite']}")
    print(f"   • Moyennement similaires : {a['nb_moyenne_similarite']}")
    print(f"   • Peu similaires : {a['nb_basse_similarite']}")
    
    # Top entreprises
    if a['entreprises_top']:
        print(f"\n🏢 ENTREPRISES IMPLIQUÉES :")
        for ent, count in list(a['entreprises_top'].items())[:3]:
            print(f"   • {ent} : {count} document(s)")
    
    # Top documents similaires
    print(f"\n🔝 TOP 3 DOCUMENTS LES PLUS SIMILAIRES :")
    for i, doc in enumerate(resultat['documents_similaires'][:3], 1):
        print(f"\n   {i}. [{doc['similarite']*100:.1f}%] {doc['titre'][:80]}")
        print(f"      Type : {doc['type_document']}")
        print(f"      Entreprise : {doc['assignee']}")
        print(f"      Année : {doc['year']}")
    
    print("\n" + "=" * 70)




