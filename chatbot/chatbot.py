# chatbot.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os

# =========================
# 1. API KEY
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =========================
# 2. Embedding Model
# =========================

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"  # <-- Version Small pour la vitesse
)

# =========================
# 3. Charger la DB vectorielle
# =========================

db = Chroma(
    persist_directory="db_vector",
    embedding_function=embedding_model
)

# =========================
# 4. Charger le LLM
# =========================

llm = ChatGroq(
    base_url="https://api.groq.com",
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=GROQ_API_KEY,
)

# =========================
# 5. Fonction de recherche
# =========================

def search_similarity(question, k=8):
    results = db.similarity_search(question, k=k)

    context = ""

    for i, doc in enumerate(results):
        context += f"\n[Document {i+1}]\n"
        context += doc.page_content.strip()
        context += "\n---\n"

    return context

# =========================
# 6. Fonction principale RAG
# =========================

def ask_question(question):

    context = search_similarity(question)

    # CORRECTION ICI : Ajout de "template" précédant le texte
    template = """
Tu es un assistant expert en propriété intellectuelle.

Réponds de manière :
- claire
- complète
- structurée
- sans couper les phrases

Utilise uniquement le contexte.

Si le contexte est incomplet, complète de manière logique SANS inventer de faits.

Format de réponse :
- définition
- explication
- importance

Contexte:
{context}

Question:
{question}

Réponse :
"""

    prompt = ChatPromptTemplate.from_template(template)

    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "question": question
    })

    return response.content

# =========================
# 7. Boucle de Chat
# =========================

print("🤖 Chatbot démarré !")
print("Tape 'exit' pour quitter.\n")


if __name__ == "__main__":
    print("🤖 Chatbot démarré !")
    print("Tape 'exit' pour quitter.\n")
 
    while True:
        question = input("Vous : ")
        if question.lower() == "exit":
            print("Fin du chatbot.")
            break
        answer = ask_question(question)
        print("\n🤖 Bot :", answer)
        print("\n" + "-"*50 + "\n")