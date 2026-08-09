# api.py - FastAPI backend pour le chatbot
# Place ce fichier dans ton dossier chatbot/ (à côté de chatbot.py)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import ask_question

app = FastAPI(title="Chatbot API - Propriété Intellectuelle")

# CORS : autoriser Angular (port 4200) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str

@app.get("/")
def root():
    return {"status": "Chatbot API en ligne ✅"}

@app.post("/chat", response_model=AnswerResponse)
def chat(request: QuestionRequest):
    answer = ask_question(request.question)
    return AnswerResponse(answer=answer)