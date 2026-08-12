# test_rag_pipeline.py
# Tests automatisés du pipeline RAG - Prior Art Search

from rag_pipeline import analyser_idee_invention
from search import get_statistics


# ══════════════════════════════════════════════════════
# JEUX DE TESTS
# ══════════════════════════════════════════════════════

TESTS = [
    {
        "nom": "Test 1 : Idée probablement existante (Pacemaker Bluetooth)",
        "idee": """A cardiac pacemaker device that monitors heart rhythm and 
        automatically sends notifications via Bluetooth to a smartphone application 
        for real-time patient monitoring.""",
        "type_document": None,
        "verdict_attendu": "IDEE_EXISTANTE"  # On s'attend à ce résultat
    },
    {
        "nom": "Test 2 : Idée nouvelle (Décodeur quantique cérébral)",
        "idee": """A quantum-based brain wave decoder that uses entangled photons 
        to read neural signals through skin without invasive electrodes, allowing 
        paralyzed patients to control robotic limbs with thoughts.""",
        "type_document": None,
        "verdict_attendu": "IDEE_NOUVELLE"
    },
    {
        "nom": "Test 3 : Recherche filtrée (Brevets uniquement)",
        "idee": """A wearable device that uses AI to detect early signs of 
        diabetes through continuous glucose monitoring via skin sensors.""",
        "type_document": "Brevet d'invention",
        "verdict_attendu": None  # On veut juste vérifier que ça marche
    }
]


# ══════════════════════════════════════════════════════
# LANCER LES TESTS
# ══════════════════════════════════════════════════════

def run_all_tests():
    """Lance tous les tests et affiche un rapport"""
    
    print("🧪 LANCEMENT DES TESTS DU PIPELINE RAG")
    print("=" * 70)
    
    # Vérification de la base
    print("\n📊 Vérification de la base ChromaDB...")
    stats = get_statistics()
    print(f"   ✅ {stats['total_chunks']} chunks disponibles")
    
    # Résultats des tests
    resultats_tests = {
        'reussis': 0,
        'echoues': 0,
        'details': []
    }
    
    for i, test in enumerate(TESTS, 1):
        print("\n\n" + "█" * 70)
        print(f"█  {test['nom']}")
        print("█" * 70)
        
        try:
            # Lancer l'analyse
            resultat = analyser_idee_invention(
                idee=test['idee'],
                type_document=test['type_document'],
                verbose=True
            )
            
            # Vérifier le verdict si attendu
            verdict_obtenu = resultat['decision']['verdict']
            
            if test['verdict_attendu']:
                if verdict_obtenu == test['verdict_attendu']:
                    statut = "✅ RÉUSSI"
                    resultats_tests['reussis'] += 1
                else:
                    statut = f"⚠️ INATTENDU (attendu: {test['verdict_attendu']}, obtenu: {verdict_obtenu})"
                    resultats_tests['echoues'] += 1
            else:
                statut = "✅ EXÉCUTÉ"
                resultats_tests['reussis'] += 1
            
            resultats_tests['details'].append({
                'nom': test['nom'],
                'statut': statut,
                'verdict': verdict_obtenu
            })
            
        except Exception as e:
            print(f"❌ ERREUR : {e}")
            resultats_tests['echoues'] += 1
            resultats_tests['details'].append({
                'nom': test['nom'],
                'statut': f"❌ ÉCHEC : {e}",
                'verdict': None
            })
    
    # ─── Rapport final ───
    print("\n\n" + "🎉" * 35)
    print("   📋 RAPPORT FINAL DES TESTS")
    print("🎉" * 35)
    
    print(f"\n✅ Tests réussis : {resultats_tests['reussis']}/{len(TESTS)}")
    print(f"❌ Tests échoués : {resultats_tests['echoues']}/{len(TESTS)}")
    
    print("\n📝 Détails :")
    for detail in resultats_tests['details']:
        print(f"   • {detail['nom']}")
        print(f"     → {detail['statut']}")
    
    print("\n" + "🎉" * 35)


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    run_all_tests() 