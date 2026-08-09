import os
from dotenv import load_dotenv
load_dotenv()
import pdfplumber
from groq import Groq
import json
import uuid
from models import AnalysisReport, NormeResult, Issue

# APRÈS (Groq)
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=120.0  # attendre jusqu'à 2 minutes au lieu de 30 secondes par défaut
)

# ─── EXTRAIRE le texte d'un PDF ───
def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # si la page a du texte
                text += f"\n--- Page {pdf.pages.index(page) + 1} ---\n"
                text += page_text
    return text

# ─── ANALYSER le document avec Claude AI ───
def analyze_document(pdf_path: str, document_name: str) -> AnalysisReport:

    # ÉTAPE 1 : extraire le texte du PDF
    text = extract_text_from_pdf(pdf_path)

    # si le texte est trop long, on prend les 15000 premiers caractères
    # (pour ne pas dépasser la limite de l'API)
    text_to_analyze = text[:15000] if len(text) > 15000 else text

    # ÉTAPE 2 : construire le message pour Claude AI
    prompt = f"""Tu es un expert en analyse de documents. Analyse ce document selon les 3 normes suivantes et retourne UNIQUEMENT un JSON valide, sans texte avant ou après.

DOCUMENT À ANALYSER :
{text_to_analyze}

NORMES À VÉRIFIER :
1. CONSISTANCE : Cohérence entre les sections (terminologie, références, numérotation)
2. PRECISION : Exactitude technique (références ISO, dates, données chiffrées)
3. REDACTION : Qualité du français (grammaire, clarté, longueur des phrases)

Retourne UNIQUEMENT ce JSON (remplace les valeurs par ton analyse réelle) :
{{
  "overallScore": 85,
  "status": "partial",
  "summary": "résumé général de l'analyse",
  "normesCovered": [
    {{
      "normeCode": "CONSISTANCE",
      "normeName": "Consistance Inter-Section",
      "passed": true,
      "score": 90,
      "details": "description de l'analyse de consistance",
      "issues": [
        {{
          "id": "issue_001",
          "severity": "minor",
          "normeRef": "CONSISTANCE",
          "description": "description du problème trouvé",
          "page": 1,
          "suggestion": "comment corriger"
        }}
      ]
    }},
    {{
      "normeCode": "PRECISION",
      "normeName": "Précision Technique",
      "passed": true,
      "score": 85,
      "details": "description de l'analyse de précision",
      "issues": []
    }},
    {{
      "normeCode": "REDACTION",
      "normeName": "Qualité Rédactionnelle",
      "passed": true,
      "score": 80,
      "details": "description de l'analyse de rédaction",
      "issues": []
    }}
  ]
}}"""

    # ÉTAPE 3 : envoyer à Claude AI et récupérer la réponse
    # APRÈS (Groq)
    message = client.chat.completions.create(
    model="llama-3.3-70b-versatile",  # modèle gratuit et très puissant
    max_tokens=4000,
    messages=[{"role": "user", "content": prompt}]
)
    response_text = message.choices[0].message.content

    # ÉTAPE 5 : nettoyer et convertir la réponse JSON
    # parfois Claude met des ```json ... ``` autour, on les enlève
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    result = json.loads(response_text.strip())

    # ÉTAPE 6 : construire le rapport final
    normes_results = []
    total_issues = 0
    critical_issues = 0

    for norme_data in result["normesCovered"]:
        issues = []
        for issue_data in norme_data.get("issues", []):
            issue = Issue(
                id=issue_data["id"],
                severity=issue_data["severity"],
                normeRef=issue_data["normeRef"],
                description=issue_data["description"],
                page=issue_data.get("page"),
                suggestion=issue_data["suggestion"]
            )
            issues.append(issue)
            total_issues += 1
            if issue_data["severity"] == "critical":
                critical_issues += 1

        norme_result = NormeResult(
            normeCode=norme_data["normeCode"],
            normeName=norme_data["normeName"],
            passed=norme_data["passed"],
            score=norme_data["score"],
            details=norme_data["details"],
            issues=issues
        )
        normes_results.append(norme_result)

    # ÉTAPE 7 : créer le rapport complet
    report = AnalysisReport(
        documentId=f"doc_{uuid.uuid4().hex[:8]}",  # id unique aléatoire
        documentName=document_name,
        overallScore=result["overallScore"],
        status=result["status"],
        totalIssues=total_issues,
        criticalIssues=critical_issues,
        summary=result["summary"],
        normesCovered=normes_results
    )

    return report