# embedding.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
# =========================
# 1. Charger tous les PDFs
# =========================

DATA_FOLDER = "data"

documents = []

for file in os.listdir(DATA_FOLDER):

    if file.endswith(".pdf"):

        pdf_path = os.path.join(DATA_FOLDER, file)

        loader = PyPDFLoader(pdf_path)

        docs = loader.load()

        documents.extend(docs)

        print(f"✅ {file} chargé avec succès")

print(f"\nNombre total de pages : {len(documents)}")

# =========================
# 2. Découpage en chunks
# =========================

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

chunks = text_splitter.split_documents(documents)

print(f"Nombre de chunks : {len(chunks)}")

# =========================
# =========================
# 3. Embedding Model
# =========================

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"  # <-- On a changé "large" par "small"
)
# =========================
# 4. Base vectorielle
# =========================

db = Chroma(
    persist_directory="db_vector",
    embedding_function=embedding_model
)

db.add_documents(chunks)

print("✅ Base vectorielle créée avec tous les PDFs !")