# api.py
# API FastAPI pour MedTech Prior Art Search
# Backend pour le projet PFE - 3 types de documents

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import des modules backend
from search import rechercher_documents, get_statistics
from llm import repondre_question, analyser_invention


# ═══════════════════════════════════════════════════
# 🚀 INITIALISATION DE L'API
# ═══════════════════════════════════════════════════

app = FastAPI(
    title="🏥 API MedTech Prior Art Search",
    description="""
    API pour l'analyse d'antériorité dans le domaine MedTech.
    
    **Fonctionnalités :**
    - 🔍 Recherche dans 23 000+ documents (Brevets, Certificats, Modèles)
    - 🤖 Analyse d'antériorité automatique (Prior Art Search)
    - 💡 Suggestions de différenciation
    - 📊 Statistiques de la base
    
    **Technologies :** ChromaDB + BGE Embeddings + Groq Llama 3.3
    """,
    version="2.0.0",
    contact={
        "name": "PFE MedTech",
        "email": "votre.email@example.com"
    }
)

# ═══════════════════════════════════════════════════
# 🌐 CONFIGURATION CORS (pour Angular 19)
# ═══════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:3000",
        "http://127.0.0.1:4200",
        "*",  # ⚠️ En dev seulement
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════
# 📋 MODÈLES DE DONNÉES (Pydantic) - VERSION CORRIGÉE
# ═══════════════════════════════════════════════════

# ────── Modèles de requête (INPUT) ──────

class SearchRequest(BaseModel):
    """Requête de recherche simple"""
    query: str = Field(..., description="La question ou les mots-clés à rechercher")
    n_results: Optional[int] = Field(5, description="Nombre de résultats à retourner")
    type_document: Optional[str] = Field(None, description="Filtrer par type")
    year_filter: Optional[str] = Field(None, description="Filtrer par année")
    assignee_filter: Optional[str] = Field(None, description="Filtrer par entreprise")


class AnalysisRequest(BaseModel):
    """Requête d'analyse Q&A (RAG + LLM)"""
    question: str = Field(..., description="La question à analyser")
    n_results: Optional[int] = Field(5, description="Nombre de documents à analyser")
    type_document: Optional[str] = Field(None, description="Filtrer par type de document")
    year_filter: Optional[str] = Field(None, description="Filtrer par année")
    assignee_filter: Optional[str] = Field(None, description="Filtrer par entreprise")


class PriorArtRequest(BaseModel):
    """Requête d'analyse d'antériorité (Prior Art Search) - Adapté Angular"""
    titre: str = Field(..., description="Titre/Nom de l'invention")
    domaine: str = Field(..., description="Domaine technique médical")
    idee: str = Field(..., description="Description complète de l'idée")
    type_brevet: Optional[str] = Field("invention", description="Type : invention, utilite, modele")


# ═══════════════════════════════════════════════════
# 🏠 ENDPOINT D'ACCUEIL
# ═══════════════════════════════════════════════════

@app.get("/", tags=["🏠 Accueil"])
def home():
    """Page d'accueil de l'API avec liste des endpoints"""
    return {
        "name": "🏥 API MedTech Prior Art Search",
        "version": "2.0.0",
        "status": "✅ Opérationnel",
        "documentation": "/docs",
        "endpoints": {
            "GET /": "Cette page",
            "GET /health": "Vérification de santé",
            "GET /stats": "Statistiques de la base",
            "GET /document-types": "Liste des types de documents",
            "POST /search": "Recherche simple (RAG sans LLM)",
            "POST /analyze": "Q&A avec LLM (RAG + Llama 3.3)",
            "POST /prior-art": "🆕 Analyse d'antériorité (Prior Art Search)"
        }
    }


# ═══════════════════════════════════════════════════
# ❤️ HEALTH CHECK
# ═══════════════════════════════════════════════════

@app.get("/health", tags=["🏠 Accueil"])
def health_check():
    """Vérifie que l'API et la base ChromaDB fonctionnent"""
    try:
        stats = get_statistics()
        return {
            "status": "healthy",
            "service": "MedTech Prior Art Search",
            "version": "2.0.0",
            "database": {
                "status": "connected",
                "total_chunks": stats['total_chunks']
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service non disponible : {str(e)}"
        )


# ═══════════════════════════════════════════════════
# 📊 STATISTIQUES
# ═══════════════════════════════════════════════════

@app.get("/stats", tags=["📊 Statistiques"])
def get_stats():
    """Retourne les statistiques complètes de la base de données."""
    try:
        stats = get_statistics()
        
        return {
            "success": True,
            "data": {
                "total_chunks": stats['total_chunks'],
                "repartition": stats['repartition'],
                "model_embedding": "BAAI/bge-large-en-v1.5",
                "model_llm": "llama-3.3-70b-versatile",
                "vector_db": "ChromaDB"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur stats : {str(e)}"
        )


# ═══════════════════════════════════════════════════
# 📋 TYPES DE DOCUMENTS DISPONIBLES
# ═══════════════════════════════════════════════════

@app.get("/document-types", tags=["📊 Statistiques"])
def get_document_types():
    """Retourne la liste des types de documents disponibles."""
    return {
        "success": True,
        "types": [
            {
                "value": "Brevet d'invention",
                "label": "📜 Brevet d'invention",
                "description": "Protection d'une invention technique (20 ans)"
            },
            {
                "value": "Certificat d'utilité",
                "label": "📋 Certificat d'utilité",
                "description": "Petit brevet rapide (10 ans)"
            },
            {
                "value": "Modèle industriel",
                "label": "🎨 Modèle industriel",
                "description": "Protection du design d'un produit"
            }
        ]
    }


# ═══════════════════════════════════════════════════
# 🔍 ENDPOINT 1 : RECHERCHE SIMPLE (RAG seul)
# ═══════════════════════════════════════════════════

@app.post("/search", tags=["🔍 Recherche"])
def search_documents(request: SearchRequest):
    """🔍 Recherche les documents les plus similaires (sans LLM, rapide)."""
    try:
        results = rechercher_documents(
            question=request.query,
            n_resultats=request.n_results,
            filtre_type=request.type_document,
            filtre_year=request.year_filter,
            filtre_assignee=request.assignee_filter
        )
        
        return {
            "success": True,
            "query": request.query,
            "filters_applied": {
                "type_document": request.type_document,
                "year": request.year_filter,
                "assignee": request.assignee_filter
            },
            "count": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de recherche : {str(e)}"
        )


# ═══════════════════════════════════════════════════
# 🤖 ENDPOINT 2 : ANALYSE Q&A (RAG + LLM)
# ═══════════════════════════════════════════════════

@app.post("/analyze", tags=["🤖 Analyse IA"])
def analyze_question(request: AnalysisRequest):
    """🤖 Analyse une question avec le LLM (RAG + Llama 3.3)."""
    try:
        result = repondre_question(
            question=request.question,
            n_resultats=request.n_results,
            type_document=request.type_document,
            filtre_year=request.year_filter,
            filtre_assignee=request.assignee_filter
        )
        
        return {
            **result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur d'analyse : {str(e)}"
        )


# ═══════════════════════════════════════════════════
# 🔬 ENDPOINT 3 : ANALYSE D'ANTÉRIORITÉ (Prior Art Search) ⭐
# ═══════════════════════════════════════════════════

@app.post("/prior-art", tags=["🔬 Prior Art"])
def prior_art_search(request: PriorArtRequest):
    """
    🔬 Analyse d'antériorité (Prior Art Search) - Adapté frontend Angular
    
    Reçoit du frontend :
    - titre : Titre de l'invention
    - domaine : Domaine technique
    - idee : Description complète (déjà formatée par Angular)
    - type_brevet : "invention", "utilite", "modele"
    """
    try:
        # ⭐ Mapper le type Angular vers le type backend
        type_mapping = {
            "invention": "Brevet d'invention",
            "utilite": "Certificat d'utilité",
            "modele": "Modèle industriel"
        }
        type_document = type_mapping.get(
            request.type_brevet.lower(), 
            "Brevet d'invention"
        )
        
        # ⭐ Construire l'idée complète à partir du formulaire Angular
        idee_complete = f"""
        Titre : {request.titre}
        Domaine : {request.domaine}
        
        {request.idee}
        """.strip()
        
        # Lancer l'analyse d'antériorité
        result = analyser_invention(
            idee=idee_complete,
            type_document=type_document
        )
        
        # Formater la réponse pour le frontend
        response = {
            "success": True,
            "input": {
                "titre": request.titre,
                "domaine": request.domaine,
                "type_brevet": request.type_brevet,
                "type_document_resolved": type_document
            },
            "verdict": {
                "code": result['verdict_automatique']['verdict'],
                "titre": result['verdict_automatique']['titre'],
                "emoji": result['verdict_automatique']['emoji'],
                "niveau_risque": result['verdict_automatique']['niveau_risque'],
                "explication": result['verdict_automatique']['explication'],
                "recommandation": result['verdict_automatique']['recommandation']
            },
            "statistiques": {
                "nb_documents_analyses": len(result['documents_similaires']),
                "similarite_max": round(result['analyse_statistique']['similarite_max'] * 100, 1),
                "similarite_moyenne": round(result['analyse_statistique']['similarite_moyenne'] * 100, 1),
                "nb_haute_similarite": result['analyse_statistique']['nb_haute_similarite'],
                "nb_moyenne_similarite": result['analyse_statistique']['nb_moyenne_similarite'],
                "nb_basse_similarite": result['analyse_statistique']['nb_basse_similarite'],
                "types_documents": result['analyse_statistique']['types_documents'],
                "entreprises_top": result['analyse_statistique']['entreprises_top']
            },
            "documents_similaires": [
                {
                    "rang": i + 1,
                    "id": doc.get('id', ''),
                    "titre": doc.get('titre', ''),
                    "type_document": doc.get('type_document', ''),
                    "assignee": doc.get('assignee', ''),
                    "year": doc.get('year', ''),
                    "cpc": doc.get('cpc', ''),
                    "similarite": round(doc.get('similarite', 0) * 100, 1),
                    "extrait": doc.get('texte', '')[:300] + "..." if len(doc.get('texte', '')) > 300 else doc.get('texte', ''),
                    "lien_google_patents": f"https://patents.google.com/patent/{doc.get('id', '')}"
                }
                for i, doc in enumerate(result['documents_similaires'][:10])
            ],
            "analyse_complete": result['reponse'],
            "metadata": result.get('metadata', {}),
            "timestamp": datetime.now().isoformat()
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur Prior Art Search : {str(e)}"
        )


# ═══════════════════════════════════════════════════
# 🚀 DÉMARRAGE DU SERVEUR
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    PORT = 8002
    HOST = "0.0.0.0"
    
    print("\n" + "═" * 70)
    print("🚀 DÉMARRAGE DE L'API MEDTECH PRIOR ART SEARCH")
    print("═" * 70)
    print(f"")
    print(f"   ⚠️  ATTENTION : Ne clique PAS sur 0.0.0.0 !")
    print(f"")
    print(f"   ✅ Utilise CES URLs dans ton navigateur :")
    print(f"")
    print(f"   🌐 Application      : http://localhost:{PORT}")
    print(f"   📚 Documentation    : http://localhost:{PORT}/docs")
    print(f"   📖 ReDoc           : http://localhost:{PORT}/redoc")
    print(f"   ❤️  Health Check    : http://localhost:{PORT}/health")
    print(f"")
    print("═" * 70 + "\n")
    
    uvicorn.run(
        "api:app",
        host=HOST,
        port=PORT,
        reload=True
    )