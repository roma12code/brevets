# llm.py
# Module LLM avec Groq + Llama 3.3 pour MedTech Prior Art Search

import os
from dotenv import load_dotenv
from groq import Groq
from search import rechercher_documents
from rag_pipeline import analyser_idee_invention

# ══════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════

load_dotenv()

# Initialisation Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

if not os.getenv("GROQ_API_KEY"):
    print("❌ GROQ_API_KEY manquante dans .env")
else:
    print(f"✅ Clé Groq détectée : {os.getenv('GROQ_API_KEY')[:10]}...")

# Paramètres LLM
MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.1   # Réponses factuelles
MAX_TOKENS = 2500   # Un peu plus pour les analyses détaillées


# ══════════════════════════════════════════════════════
# FONCTION 1 : Mode Q&A (Question/Réponse classique)
# ══════════════════════════════════════════════════════

def repondre_question(question: str, n_resultats=5, type_document=None, filtre_year=None, filtre_assignee=None):
    """
    Mode Q&A : Répond à une question sur les documents MedTech.
    
    Args:
        question (str): Question de l'utilisateur
        n_resultats (int): Nombre de documents à analyser
        type_document (str): Filtrer par type ("Brevet d'invention", etc.)
        filtre_year (str): Filtrer par année
        filtre_assignee (str): Filtrer par entreprise
    
    Returns:
        dict: Réponse structurée
    """
    print(f"\n🔍 Recherche dans ChromaDB pour : '{question[:80]}...'")
    
    # Recherche avec filtres optionnels
    resultats = rechercher_documents(
        question=question, 
        n_resultats=n_resultats,
        filtre_type=type_document,
        filtre_year=filtre_year,
        filtre_assignee=filtre_assignee
    )
    
    print(f"✅ {len(resultats)} documents trouvés")
    
    if not resultats:
        return {
            "success": False,
            "mode": "qa",
            "reponse": "Aucun document trouvé pour votre recherche. Essayez avec d'autres mots-clés.",
            "documents_trouves": []
        }
    
    # Construction du contexte
    contexte = construire_contexte(resultats)
    
    # Prompts
    system_prompt = get_system_prompt_qa(type_document)
    user_prompt = f"""Contexte des documents trouvés :

{contexte}

Question de l'utilisateur : {question}

Analyse ces documents et réponds à la question de manière structurée et professionnelle."""
    
    # Appel au LLM
    return appeler_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        question=question,
        resultats=resultats,
        mode="qa"
    )


# ══════════════════════════════════════════════════════
# FONCTION 2 : Mode Prior Art (Analyse d'antériorité)
# ══════════════════════════════════════════════════════

def analyser_invention(idee: str, type_document=None):
    """
    Mode Prior Art : Analyse si une idée d'invention existe déjà.
    
    Args:
        idee (str): Description de l'invention proposée
        type_document (str): Filtrer par type de document
    
    Returns:
        dict: Analyse complète avec verdict et recommandations
    """
    print(f"\n🔬 Analyse d'antériorité pour : '{idee[:80]}...'")
    
    # 1. Lancer le pipeline RAG (recherche + décision automatique)
    resultat_pipeline = analyser_idee_invention(
        idee=idee,
        type_document=type_document,
        verbose=False  # Pas d'affichage console
    )
    
    # 2. Récupérer le contexte préparé par le pipeline
    contexte_llm = resultat_pipeline['contexte_pour_llm']
    
    # 3. System prompt spécialisé pour l'analyse d'antériorité
    system_prompt = get_system_prompt_prior_art()
    
    # 4. Appel au LLM avec le contexte enrichi
    response_llm = appeler_llm(
        system_prompt=system_prompt,
        user_prompt=contexte_llm,
        question=idee,
        resultats=resultat_pipeline['documents_similaires'],
        mode="prior_art"
    )
    
    # 5. Enrichir la réponse avec les données du pipeline
    response_llm['verdict_automatique'] = resultat_pipeline['decision']
    response_llm['analyse_statistique'] = resultat_pipeline['analyse_statistique']
    response_llm['documents_similaires'] = resultat_pipeline['documents_similaires']
    
    return response_llm


# ══════════════════════════════════════════════════════
# FONCTION 3 : Construire le contexte
# ══════════════════════════════════════════════════════

def construire_contexte(resultats):
    """Formate les résultats pour le LLM"""
    contexte_parts = []
    
    for i, r in enumerate(resultats, 1):
        partie = f"""=== Document {i} ===
Type : {r.get('type_document', 'N/A')}
Titre : {r.get('titre', 'N/A')}
Propriétaire : {r.get('assignee', 'N/A')}
Année : {r.get('year', 'N/A')}
Code CPC : {r.get('cpc', 'N/A')}
Similarité : {r.get('similarite', 0)*100:.1f}%
Contenu : {r.get('texte', '')[:500]}..."""
        contexte_parts.append(partie)
    
    return "\n\n".join(contexte_parts)


# ══════════════════════════════════════════════════════
# FONCTION 4 : Prompts système
# ══════════════════════════════════════════════════════

def get_system_prompt_qa(type_document=None):
    """System prompt pour le mode Q&A classique"""
    
    type_info = ""
    if type_document:
        type_info = f"\n📌 Tu analyses uniquement des documents de type : {type_document}"
    
    return f"""Tu es un auditeur expert en propriété intellectuelle et technologies médicales (MedTech).{type_info}

🎯 Ta mission : Répondre aux questions sur les brevets, certificats d'utilité et modèles industriels MedTech.

🚫 Règles absolues :
1. Tu réponds UNIQUEMENT à partir des documents fournis dans le contexte.
2. Tu n'inventes JAMAIS d'informations.
3. Si tu ne sais pas, dis-le clairement.
4. Tu cites toujours les sources (numéro de document, titre).

📋 Structure de tes réponses :
   📝 **Résumé** : Synthèse en 2-3 phrases
   🔍 **Analyse détaillée** : Points clés issus des documents
   ⚠️ **Risques détectés** : Conflits potentiels, brevets bloquants
   ✅ **Points positifs** : Opportunités identifiées
   💡 **Recommandations** : Actions concrètes à entreprendre
   📚 **Sources** : Liste des documents cités

✍️ Style : Professionnel, clair, en français, structuré avec markdown."""


def get_system_prompt_prior_art():
    """System prompt pour le mode Analyse d'antériorité"""
    
    return """Tu es un expert en propriété intellectuelle spécialisé dans l'analyse d'antériorité (Prior Art Search) pour le domaine MedTech (technologies médicales).

🎯 Ta mission : Analyser si une idée d'invention est nouvelle ou si elle existe déjà dans la base de brevets/certificats/modèles industriels.

🚫 Règles absolues :
1. Tu te bases UNIQUEMENT sur les documents fournis.
2. Tu n'inventes AUCUN brevet ou information.
3. Tu cites les documents par leur titre/numéro.
4. Tu es objectif : ni trop optimiste, ni trop pessimiste.

📋 Structure OBLIGATOIRE de ta réponse :

## 🔍 1. ANALYSE D'ANTÉRIORITÉ
- L'idée existe-t-elle déjà ? Réponse claire (Oui/Non/Partiellement)
- Justification basée sur les documents trouvés
- Brevets les plus pertinents (avec titres)

## 💡 2. DIFFÉRENCIATION POSSIBLE
- Comment l'inventeur peut différencier son idée des existantes
- Aspects innovants qui pourraient être protégés
- Combinaisons originales possibles

## ⚖️ 3. ANALYSE DE BREVETABILITÉ
- ✅ **Nouveauté** : L'idée est-elle nouvelle ? (Justifier)
- ✅ **Activité inventive** : Est-elle non-évidente pour un expert ? (Justifier)
- ✅ **Application industrielle** : Est-elle réalisable ? (Justifier)

## 🎯 4. RECOMMANDATIONS STRATÉGIQUES
- Faut-il continuer le développement ? (Oui/Non/Modifier)
- Classifications CPC suggérées
- Concurrents principaux à surveiller
- Marchés géographiques pertinents

## 📋 5. CONCLUSION
- Verdict final clair
- Niveau de risque (Faible/Moyen/Élevé)
- 3 prochaines étapes recommandées

✍️ Style : Professionnel, en français, avec markdown pour la lisibilité."""


# ══════════════════════════════════════════════════════
# FONCTION 5 : Appel générique au LLM
# ══════════════════════════════════════════════════════

def appeler_llm(system_prompt, user_prompt, question, resultats, mode="qa"):
    """Fait l'appel à Groq + Llama 3.3"""
    
    try:
        print(f"🤖 Appel à Groq ({MODEL_NAME}) en mode '{mode}'...")
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        reponse_text = response.choices[0].message.content
        
        # Stats de l'appel
        tokens_utilises = response.usage.total_tokens if hasattr(response, 'usage') else 0
        
        print(f"✅ Réponse générée ({tokens_utilises} tokens utilisés)")
        
        return {
            "success": True,
            "mode": mode,
            "question": question,
            "reponse": reponse_text,
            "documents_trouves": resultats,
            "metadata": {
                "model": MODEL_NAME,
                "tokens_utilises": tokens_utilises,
                "nb_documents": len(resultats)
            }
        }
        
    except Exception as e:
        print(f"❌ ERREUR LLM : {str(e)}")
        return {
            "success": False,
            "mode": mode,
            "question": question,
            "reponse": f"Erreur lors de l'appel au LLM : {str(e)}",
            "documents_trouves": resultats,
            "error": str(e)
        }
