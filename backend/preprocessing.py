import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import re
import os
import matplotlib.pyplot as plt
from config import CONFIGS, RENAMING, KEYWORDS_MEDTECH

# ══════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES (votre code original)
# ══════════════════════════════════════════════════════

def check_empty(df, etape_nom):
    if df.empty:
        print(f"\n❌ ERREUR : DataFrame vide après '{etape_nom}' !")
        sys.exit(1)
    else:
        print(f"     ℹ️  Lignes restantes : {len(df)}")

def harmonize(df):
    if df.empty:
        return df
    df = df.rename(columns={k: v for k, v in RENAMING.items() if k in df.columns})
    cols = [c for c in ["id","title","abstract","date","assignee","cpc"] if c in df.columns]
    return df[cols]

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\s\.\,\;\:\(\)\-\/\%]', ' ', text)
    return text.strip()

def is_medtech(text):
    text = str(text).lower()
    return any(kw in text for kw in KEYWORDS_MEDTECH)

# ══════════════════════════════════════════════════════
# FONCTION PRINCIPALE — Traite UN type de document
# ══════════════════════════════════════════════════════

def process_document_type(doc_type, config):
    """
    Traite un type de document selon sa configuration.
    
    Args:
        doc_type (str): "brevets", "certificats_utilite" ou "modeles_industriels"
        config (dict): Configuration du type de document
    """
    
    print("\n" + "=" * 60)
    print(f"   🚀 TRAITEMENT : {config['type_document'].upper()}")
    print("=" * 60)
    
    # ─── ÉTAPE 1 : Charger les fichiers ───
    print("\n📂 ÉTAPE 1 — Chargement des fichiers...")
    
    dataframes = []
    for filename in config['input_files']:
        filepath = os.path.join(config['input_folder'], filename)
        try:
            df_temp = pd.read_csv(filepath, encoding="utf-8")
            print(f"  ✅ {filename} : {len(df_temp)} lignes")
            print(f"     Colonnes : {df_temp.columns.tolist()[:5]}...")
            dataframes.append(df_temp)
        except Exception as e:
            print(f"  ⚠️  Erreur sur {filename} : {e}")
    
    if not dataframes:
        print(f"❌ Aucun fichier chargé pour {doc_type}")
        return None
    
    # ─── ÉTAPE 2 : Harmoniser ───
    print("\n🔧 ÉTAPE 2 — Harmonisation des colonnes...")
    dataframes = [harmonize(df) for df in dataframes]
    
    # ─── ÉTAPE 3 : Fusionner ───
    print("\n🔗 ÉTAPE 3 — Fusion...")
    df = pd.concat(dataframes, ignore_index=True)
    print(f"  Total : {len(df)} documents")
    check_empty(df, "Fusion")
    
    # ─── ÉTAPE 4 : Nettoyage ───
    print("\n🧹 ÉTAPE 4 — Nettoyage...")
    etapes = {"01_initial": len(df)}
    
    # 4.1 Doublons
    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"])
    etapes["02_sans_doublons"] = len(df)
    print(f"  ✅ Doublons supprimés : {etapes['01_initial'] - etapes['02_sans_doublons']}")
    check_empty(df, "Doublons")
    
    # 4.2 Abstracts vides (ATTENTION : flexible pour les modèles industriels !)
    if "abstract" in df.columns:
        df = df.dropna(subset=["abstract"])
        df = df[df["abstract"].astype(str).str.strip().str.len() > 0]
    else:
        print("  ⚠️  Pas de colonne 'abstract' — on utilise le titre uniquement")
    
    # 4.3 Titres vides
    if "title" in df.columns:
        df = df.dropna(subset=["title"])
        df = df[df["title"].astype(str).str.strip().str.len() > 0]
    etapes["03_sans_vides"] = len(df)
    check_empty(df, "Vides")
    
    # 4.4 Nettoyage texte
    if "abstract" in df.columns:
        df["abstract"] = df["abstract"].apply(clean_text)
    if "title" in df.columns:
        df["title"] = df["title"].apply(clean_text)
    
    # ── 4.5 Longueur (Intelligent : s'applique uniquement aux abstracts) ──
    if "abstract" in df.columns:
        # On a un abstract : on applique le filtre min/max words
        df["word_count"] = df["abstract"].apply(lambda x: len(str(x).split()))
        avant = len(df)
        df = df[df["word_count"].between(config['min_words'], config['max_words'])]
        etapes["05_longueur_ok"] = len(df)
        print(f"  ✅ Abstracts hors limites supprimés : {avant - etapes['05_longueur_ok']}")
        check_empty(df, "Longueur")
    else:
        # On n'a que le titre (Certificats/Modèles) : on compte les mots pour les stats, 
        # mais on NE SUPPRIME RIEN, peu importe la longueur.
        print("  ℹ️ Pas d'abstract détecté. On garde tous les titres (filtre de longueur ignoré).")
        df["word_count"] = df["title"].apply(lambda x: len(str(x).split()))
        etapes["05_longueur_ok"] = len(df)

    # ── 4.6 Dates (Strict : on supprime les dates invalides ou hors limites) ──
    if "date" in df.columns:
        df["date"] = df["date"].astype(str)
        df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
        df["year"] = df["date_parsed"].dt.year
        
        avant = len(df)
        # On garde UNIQUEMENT les années entre 2000 et 2024. Les NaN (invalides) sont supprimés.
        df = df[df["year"].between(*config['year_range'])]
        
        etapes["06_dates_ok"] = len(df)
        print(f"  ✅ Dates invalides/hors limites supprimées : {avant - etapes['06_dates_ok']}")
        check_empty(df, "Dates")
    else:
        etapes["06_dates_ok"] = len(df)
        print("  ⚠️  Pas de colonne 'date' — étape ignorée")
    
    # 4.7 Filtre MedTech (seulement pour brevets)
    if config['apply_medtech_filter'] and "abstract" in df.columns:
        avant = len(df)
        df = df[df["abstract"].apply(is_medtech)]
        etapes["07_medtech"] = len(df)
        print(f"  ✅ Non-MedTech filtrés : {avant - etapes['07_medtech']}")
        check_empty(df, "MedTech")
    
    df = df.reset_index(drop=True)
    
    # ─── ÉTAPE 5 : Métadonnée + RAG ───
    print("\n🤖 ÉTAPE 5 — Préparation RAG...")
    
    # ⭐ LA CLÉ : Ajouter le type de document (pour le RAG plus tard)
    df["type_document"] = config['type_document']
    
    if "title" in df.columns and "abstract" in df.columns:
        df["text_for_rag"] = (
            f"[{config['type_document']}] " +
            "TITLE: " + df["title"].fillna("") +
            "\nABSTRACT: " + df["abstract"].fillna("")
        )
    elif "title" in df.columns:
        df["text_for_rag"] = (
            f"[{config['type_document']}] " +
            "TITLE: " + df["title"].fillna("")
        )
    
    print("  ✅ Colonne 'text_for_rag' créée avec étiquette")
    
    # ─── ÉTAPE 6 : Sauvegarde ───
    print("\n💾 ÉTAPE 6 — Sauvegarde...")
    os.makedirs(os.path.dirname(config['output_file']), exist_ok=True)
    df.to_csv(config['output_file'], index=False, encoding="utf-8-sig")
    print(f"  ✅ {config['output_file']} ({len(df)} lignes)")
    
    # ─── ÉTAPE 7 : Graphique ───
    print("\n📊 ÉTAPE 7 — Graphique...")
    os.makedirs(os.path.dirname(config['report_image']), exist_ok=True)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"Analyse - {config['type_document']}", fontweight="bold")
    
    if "year" in df.columns:
        year_counts = df["year"].value_counts().sort_index()
        axes[0].bar(year_counts.index.astype(str), year_counts.values, color="#028090")
        axes[0].set_title("Par année")
        axes[0].tick_params(axis="x", rotation=45)
    
    axes[1].hist(df["word_count"], bins=30, color="#02C39A")
    axes[1].set_title("Longueur des textes")
    
    plt.tight_layout()
    plt.savefig(config['report_image'], dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ Graphique sauvegardé")
    
    return df


# ══════════════════════════════════════════════════════
# FONCTION FINALE — Fusionner les 3 datasets nettoyés
# ══════════════════════════════════════════════════════

def create_master_dataset(dataframes_dict):
    """Crée le Master Dataset final pour le RAG"""
    print("\n" + "=" * 60)
    print("   🌟 CRÉATION DU MASTER DATASET")
    print("=" * 60)
    
    valid_dfs = [df for df in dataframes_dict.values() if df is not None]
    df_master = pd.concat(valid_dfs, ignore_index=True)
    
    output_path = "2_Clean_Data/MASTER_DATASET_MedTech.csv"
    df_master.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ Master Dataset créé : {output_path}")
    print(f"📊 Total : {len(df_master)} documents")
    print("\nRépartition :")
    print(df_master['type_document'].value_counts())
    
    return df_master


# ══════════════════════════════════════════════════════
# MAIN — Lancer le pipeline complet
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀 PIPELINE DE NETTOYAGE COMPLET - PFE MedTech")
    print("=" * 60)
    
    results = {}
    
    # Traiter les 3 types de documents
    for doc_type, config in CONFIGS.items():
        try:
            results[doc_type] = process_document_type(doc_type, config)
        except Exception as e:
            print(f"\n❌ Erreur sur {doc_type} : {e}")
            results[doc_type] = None
    
    # Créer le Master Dataset
    create_master_dataset(results)
    
    print("\n" + "🎉" * 30)
    print("   PIPELINE TERMINÉ AVEC SUCCÈS !")
    print("🎉" * 30)