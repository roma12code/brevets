import json
import os
from models import AnalysisReport, HistoryItem
from datetime import datetime

# nom du fichier où on sauvegarde l'historique
HISTORY_FILE = "history.json"

# ─── LIRE tout l'historique depuis le fichier ───
def load_history() -> list:
    # si le fichier n'existe pas encore, on retourne une liste vide
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ─── ÉCRIRE l'historique dans le fichier ───
def save_history(history: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        # ensure_ascii=False → pour garder les accents français
        # indent=2 → pour que le fichier soit lisible

# ─── AJOUTER une nouvelle analyse à l'historique ───
def add_to_history(report: AnalysisReport):
    history = load_history()  # on charge l'historique existant

    # on crée un résumé court pour l'historique
    new_item = {
        "id": report.documentId,
        "title": report.documentName,
        "lastMessage": f"Score: {report.overallScore}% - {report.status}",
        "date": datetime.now().isoformat(),  # date et heure maintenant
        "documentsCount": 1,
        "status": report.status
    }

    history.append(new_item)   # on ajoute au début de la liste
    save_history(history)      # on sauvegarde

# ─── RÉCUPÉRER un rapport complet par son ID ───
def get_report_by_id(report_id: str):
    # on cherche dans un dossier "reports" où on sauvegarde les rapports complets
    report_file = f"reports/{report_id}.json"
    if not os.path.exists(report_file):
        return None
    with open(report_file, "r", encoding="utf-8") as f:
        return json.load(f)

# ─── SAUVEGARDER un rapport complet ───
def save_report(report: AnalysisReport):
    # créer le dossier "reports" s'il n'existe pas
    os.makedirs("reports", exist_ok=True)
    report_file = f"reports/{report.documentId}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)

# ─── SUPPRIMER une analyse de l'historique ───
def delete_from_history(report_id: str) -> bool:
    history = load_history()
    # on garde tout SAUF l'élément avec cet id
    new_history = [item for item in history if item["id"] != report_id]

    if len(new_history) == len(history):
        return False  # rien supprimé → id introuvable

    save_history(new_history)

    # supprimer aussi le rapport complet
    report_file = f"reports/{report_id}.json"
    if os.path.exists(report_file):
        os.remove(report_file)

    return True