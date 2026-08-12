# config.py
# Configuration centralisée pour le preprocessing des 3 types de documents

CONFIGS = {
    "brevets": {
        "type_document": "Brevet d'invention",
        "input_folder": "1_Raw_Data/brevets/",
        "input_files": ["ggl patent 2 5000.csv", "google patents data.csv"],
        "output_file": "2_Clean_Data/brevets_CLEAN.csv",
        "report_image": "3_Reports/rapport_brevets.png",
        "min_words": 30,
        "max_words": 700,
        "year_range": (2000, 2024),
        "apply_medtech_filter": True,  # Les brevets ne sont pas tous MedTech
    },
    
    "certificats_utilite": {
        "type_document": "Certificat d'utilité",
        "input_folder": "1_Raw_Data/certificats_utilite/",
        "input_files": ["certificats_utilite_medtech.csv"],
        "output_file": "2_Clean_Data/certificats_utilite_CLEAN.csv",
        "report_image": "3_Reports/rapport_certificats.png",
        "min_words": 10,   # Les certificats ont souvent des abstracts plus courts
        "max_words": 700,
        "year_range": (2000, 2024),
        "apply_medtech_filter": False,  # Déjà filtrés MedTech via Google Patents
    },
    
    "modeles_industriels": {
        "type_document": "Modèle industriel",
        "input_folder": "1_Raw_Data/modeles_industriels/",
        "input_files": ["modeles_industriels_medtech.csv"],
        "output_file": "2_Clean_Data/modeles_industriels_CLEAN.csv",
        "report_image": "3_Reports/rapport_modeles.png",
        "min_words": 5,    # Les designs ont des descriptions TRÈS courtes
        "max_words": 500,
        "year_range": (2000, 2024),
        "apply_medtech_filter": False,  # Déjà filtrés MedTech via Google Patents
    }
}

# Dictionnaire de renommage commun (votre code original)
RENAMING = {
    "inventionTitle"        : "title",
    "invention_title"       : "title",
    "patent_title"          : "title",
    "Title"                 : "title",
    "abstractText"          : "abstract",
    "patent_abstract"       : "abstract",
    "Abstract"              : "abstract",
    "abstract_localized"    : "abstract",
    "publicationDate"       : "date",
    "publication_date"      : "date",
    "patent_date"           : "date",
    "Date"                  : "date",
    "publication date"      : "date",  # NEW : Format Google Patents
    "publicationNumber"     : "id",
    "publication_number"    : "id",
    "patent_id"             : "id",
    "patent_number"         : "id",
    "assignee_organization" : "assignee",
    "Assignee"              : "assignee",
    "cpc_subgroup_id"       : "cpc",
    "cpc_code"              : "cpc",
    "classification"        : "cpc",
}

# Mots-clés MedTech
KEYWORDS_MEDTECH = [
    "medical", "patient", "clinical", "diagnosis",
    "health", "disease", "drug", "therapy", "surgical",
    "implant", "monitoring", "treatment", "imaging",
    "diagnostic", "hospital", "wearable", "cardiac",
    "tissue", "blood", "neural", "anatomical"
]