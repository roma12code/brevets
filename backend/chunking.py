# chunking_tokens.py
# Chunking universel pour Brevets, Certificats et Modèles Industriels

import pandas as pd
import tiktoken
import json
import os

# Initialiser le tokenizer (compatible OpenAI)
encoding = tiktoken.get_encoding("cl100k_base")

# ══════════════════════════════════════════════════════
# FONCTION 1 : Construire les métadonnées de manière flexible
# ══════════════════════════════════════════════════════

def build_metadata(row, is_chunk=False, chunk_index=None):
    """
    Construit les métadonnées d'un chunk en gérant les colonnes manquantes.
    Certains documents n'ont pas 'cpc' ou 'abstract', on s'adapte !
    """
    metadata = {
        'id': str(row.get('id', 'unknown')),
        'title': str(row.get('title', '')),
        'type_document': str(row.get('type_document', 'unknown')),  # ⭐ TRÈS IMPORTANT pour le RAG
        'is_chunk': is_chunk
    }
    
    # Ajouter les colonnes optionnelles SI elles existent
    if 'assignee' in row and pd.notna(row['assignee']):
        metadata['assignee'] = str(row['assignee'])
    
    if 'cpc' in row and pd.notna(row['cpc']):
        metadata['cpc'] = str(row['cpc'])
    
    if 'year' in row and pd.notna(row['year']):
        metadata['year'] = str(int(row['year'])) if isinstance(row['year'], float) else str(row['year'])
    
    if 'inventor/author' in row and pd.notna(row['inventor/author']):
        metadata['inventor'] = str(row['inventor/author'])
    
    if is_chunk and chunk_index is not None:
        metadata['chunk_index'] = chunk_index
    
    return metadata


# ══════════════════════════════════════════════════════
# FONCTION 2 : Chunking d'un document (universel)
# ══════════════════════════════════════════════════════

def chunk_document(row, chunk_size=500, overlap=75):
    """
    Découpe un document en chunks basés sur les tokens.
    Fonctionne pour Brevets, Certificats et Modèles Industriels.
    """
    chunks = []
    text = str(row['text_for_rag'])
    
    # Convertir texte → tokens
    tokens = encoding.encode(text)
    token_count = len(tokens)
    
    # ⭐ CAS 1 : Texte court (Certificats/Modèles ou petits brevets) → PAS de chunking
    if token_count <= chunk_size:
        chunks.append({
            'text': text,
            'chunk_id': f"{row['id']}_0",
            'token_count': token_count,
            'metadata': build_metadata(row, is_chunk=False)
        })
    
    # ⭐ CAS 2 : Texte long (gros brevets) → Chunking avec overlap
    else:
        step = chunk_size - overlap
        
        for i, start in enumerate(range(0, token_count, step)):
            chunk_tokens = tokens[start:start + chunk_size]
            chunk_text = encoding.decode(chunk_tokens)
            
            chunks.append({
                'text': chunk_text,
                'chunk_id': f"{row['id']}_{i}",
                'token_count': len(chunk_tokens),
                'metadata': build_metadata(row, is_chunk=True, chunk_index=i)
            })
    
    return chunks


# ══════════════════════════════════════════════════════
# FONCTION 3 : Traiter UN fichier CSV complet
# ══════════════════════════════════════════════════════

def process_csv_file(input_file, output_file, chunk_size=500, overlap=75):
    """
    Lit un fichier CSV nettoyé et génère ses chunks au format JSON.
    """
    print(f"\n📄 Traitement de : {input_file}")
    
    # Charger le CSV
    df = pd.read_csv(input_file)
    print(f"   📊 {len(df)} documents à chunker")
    
    # Vérifier que la colonne 'text_for_rag' existe
    if 'text_for_rag' not in df.columns:
        print(f"   ❌ Erreur : colonne 'text_for_rag' manquante dans {input_file}")
        return None
    
    # Chunker chaque document
    all_chunks = []
    total_tokens = 0
    docs_chunked = 0  # Documents qui ont été découpés en plusieurs chunks
    
    for idx, row in df.iterrows():
        chunks = chunk_document(row, chunk_size=chunk_size, overlap=overlap)
        all_chunks.extend(chunks)
        
        # Stats
        for c in chunks:
            total_tokens += c['token_count']
        if len(chunks) > 1:
            docs_chunked += 1
        
        # Affichage progression
        if (idx + 1) % 1000 == 0:
            print(f"   ⏳ {idx + 1}/{len(df)} documents traités...")
    
    # Sauvegarder en JSON
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    # Rapport
    print(f"   ✅ {len(all_chunks)} chunks créés")
    print(f"   📈 {docs_chunked} documents découpés en plusieurs chunks")
    print(f"   🔢 Total tokens : {total_tokens:,}")
    print(f"   💾 Sauvegardé : {output_file}")
    
    return all_chunks


# ══════════════════════════════════════════════════════
# MAIN : Lancer le chunking sur les 3 types de documents
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    
    print("=" * 60)
    print("   🧩 CHUNKING UNIVERSEL - PFE MedTech")
    print("=" * 60)
    
    # Configuration des fichiers à traiter
    FILES_TO_PROCESS = [
        {
            "name": "Brevets d'invention",
            "input": "2_Clean_Data/brevets_CLEAN.csv",
            "output": "4_Chunks/brevets_chunks.json",
            "chunk_size": 500,   # Brevets ont des abstracts longs
            "overlap": 75
        },
        {
            "name": "Certificats d'utilité",
            "input": "2_Clean_Data/certificats_utilite_CLEAN.csv",
            "output": "4_Chunks/certificats_chunks.json",
            "chunk_size": 500,   # Pas de chunking en pratique (titres courts)
            "overlap": 75
        },
        {
            "name": "Modèles industriels",
            "input": "2_Clean_Data/modeles_industriels_CLEAN.csv",
            "output": "4_Chunks/modeles_chunks.json",
            "chunk_size": 500,
            "overlap": 75
        }
    ]
    
    # Traiter chaque type
    all_results = {}
    for config in FILES_TO_PROCESS:
        print(f"\n{'='*60}")
        print(f"   📂 {config['name'].upper()}")
        print(f"{'='*60}")
        
        result = process_csv_file(
            input_file=config['input'],
            output_file=config['output'],
            chunk_size=config['chunk_size'],
            overlap=config['overlap']
        )
        all_results[config['name']] = result
    
    # ⭐ BONUS : Créer un MASTER fichier JSON combinant tous les chunks
    print(f"\n{'='*60}")
    print(f"   🌟 CRÉATION DU MASTER FICHIER DE CHUNKS")
    print(f"{'='*60}")
    
    master_chunks = []
    for name, chunks in all_results.items():
        if chunks:
            master_chunks.extend(chunks)
    
    master_output = "4_Chunks/MASTER_chunks.json"
    with open(master_output, 'w', encoding='utf-8') as f:
        json.dump(master_chunks, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Master fichier créé : {master_output}")
    print(f"📊 TOTAL : {len(master_chunks)} chunks au total")
    
    # Statistiques par type
    print("\n📈 Répartition des chunks par type :")
    from collections import Counter
    types_count = Counter([c['metadata']['type_document'] for c in master_chunks])
    for doc_type, count in types_count.items():
        print(f"   • {doc_type} : {count} chunks")
    
    print("\n" + "🎉" * 30)
    print("   CHUNKING TERMINÉ !")
    print("🎉" * 30)