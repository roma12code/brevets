from pydantic import BaseModel
from typing import List, Optional

# ─── UN PROBLÈME DÉTECTÉ dans le document ───
class Issue(BaseModel):
    id: str                  # identifiant unique ex: "issue_001"
    severity: str            # gravité : "critical", "major", "minor", "info"
    normeRef: str            # à quelle norme il appartient ex: "CONSISTANCE"
    description: str         # explication du problème
    page: Optional[int]      # numéro de page concernée (optionnel)
    suggestion: str          # comment corriger le problème

# ─── RÉSULTAT D'UNE NORME (une des 3) ───
class NormeResult(BaseModel):
    normeCode: str           # "CONSISTANCE", "PRECISION" ou "REDACTION"
    normeName: str           # nom complet de la norme
    passed: bool             # True = respectée, False = non respectée
    score: int               # score de 0 à 100
    details: str             # résumé de l'analyse
    issues: List[Issue]      # liste des problèmes trouvés

# ─── RAPPORT COMPLET (ce qu'on renvoie au frontend) ───
class AnalysisReport(BaseModel):
    documentId: str              # identifiant unique du document
    documentName: str            # nom du fichier PDF
    overallScore: int            # score global de 0 à 100
    status: str                  # "compliant", "partial", "non-compliant"
    totalIssues: int             # nombre total de problèmes
    criticalIssues: int          # nombre de problèmes critiques
    summary: str                 # résumé général
    normesCovered: List[NormeResult]  # résultats des 3 normes

# ─── UN ÉLÉMENT DE L'HISTORIQUE ───
class HistoryItem(BaseModel):
    id: str                  # identifiant
    title: str               # nom du document
    lastMessage: str         # résumé court ex: "Score: 85% - Partiel"
    date: str                # date de l'analyse
    documentsCount: int      # toujours 1 dans notre cas
    status: str              # "compliant", "partial", "non-compliant"