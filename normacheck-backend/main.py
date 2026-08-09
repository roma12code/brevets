import os
from dotenv import load_dotenv
load_dotenv()
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

from models import AnalysisReport
from analyzer import analyze_document
from storage import (
    add_to_history, load_history,
    get_report_by_id, save_report,
    delete_from_history
)

# ─── CRÉER L'APPLICATION FASTAPI ───
app = FastAPI(title="NormaCheck AI", version="1.0.0")

# ─── CORS : autoriser Angular à communiquer avec le backend ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ─── ENDPOINT 1 : Analyser un document PDF ───
@app.post("/api/documents/analyze")
async def analyze(
    file: UploadFile = File(...),
    normes: str = Form(...)
):
    # vérifier que c'est bien un PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Seuls les fichiers PDF sont acceptés")

    # vérifier la taille (max 50 MB)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 50 MB)")

    # sauvegarder le PDF temporairement sur le disque
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)

    try:
        # analyser le document
        report = analyze_document(temp_path, file.filename)

        # sauvegarder le rapport complet
        save_report(report)

        # ajouter à l'historique
        add_to_history(report)

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse: {str(e)}")

    finally:
        # supprimer le fichier temporaire dans tous les cas
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ─── ENDPOINT 2 : Récupérer l'historique ───
@app.get("/api/history")
def get_history():
    return load_history()

# ─── ENDPOINT 3 : Récupérer un rapport par son ID ───
@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    return report

# ─── ENDPOINT 4 : Supprimer une analyse ───
@app.delete("/api/history/{report_id}")
def delete_report(report_id: str):
    success = delete_from_history(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="ID non trouvé")
    return JSONResponse(status_code=204, content=None)

# ─── ENDPOINT 5 : Chat avec le document ───
@app.post("/api/chat")
def chat(body: dict):
    return {
        "response": "Les normes disponibles sont : Consistance Inter-Section, Précision Technique et Qualité Rédactionnelle."
    }

# ─── ENDPOINT 6 : Liste des normes disponibles ───
@app.get("/api/normes")
def get_normes():
    return [
        {"code": "CONSISTANCE", "name": "Consistance Inter-Section",
         "icon": "🔗", "description": "Cohérence entre les sections"},
        {"code": "PRECISION",   "name": "Précision Technique",
         "icon": "🎯", "description": "Exactitude des informations techniques"},
        {"code": "REDACTION",   "name": "Qualité Rédactionnelle",
         "icon": "✍️", "description": "Français simple et clair"}
    ]

# ─── LANCER LE SERVEUR ───
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)