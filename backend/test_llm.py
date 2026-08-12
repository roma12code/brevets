# test_llm.py
# Tests du module LLM (Groq + Llama 3.3)

from llm import repondre_question, analyser_invention


def test_qa_mode():
    """Test du mode Q&A classique"""
    print("\n" + "█" * 70)
    print("█  TEST 1 : Mode Q&A classique")
    print("█" * 70)
    
    result = repondre_question(
        question="Quels sont les brevets sur les pacemakers cardiaques ?",
        n_resultats=3
    )
    
    print("\n📋 RÉPONSE :\n")
    print(result['reponse'])
    print(f"\n📊 Métadonnées : {result['metadata']}")


def test_qa_avec_filtres():
    """Test du mode Q&A avec filtres"""
    print("\n" + "█" * 70)
    print("█  TEST 2 : Mode Q&A avec filtres (Brevets uniquement)")
    print("█" * 70)
    
    result = repondre_question(
        question="Innovations en chirurgie robotique",
        n_resultats=3,
        type_document="Brevet d'invention"
    )
    
    print("\n📋 RÉPONSE :\n")
    print(result['reponse'])


def test_prior_art_existant():

    """Test analyse d'antériorité - idée existante"""
    print("\n" + "█" * 70)
    print("█  TEST 3 : Prior Art - Idée probablement existante")
    print("█" * 70)
    
    idee = """A cardiac pacemaker device that monitors heart rhythm and 
    automatically sends notifications via Bluetooth to a smartphone application 
    for real-time patient monitoring."""
    
    result = analyser_invention(idee=idee)
    
    print(f"\n⚖️ VERDICT AUTOMATIQUE : {result['verdict_automatique']['titre']}")
    print(f"   Risque : {result['verdict_automatique']['niveau_risque']}\n")
    print("📋 ANALYSE DU LLM :\n")
    print(result['reponse'])


def test_prior_art_nouvelle():
    """Test analyse d'antériorité - idée nouvelle"""
    print("\n" + "█" * 70)
    print("█  TEST 4 : Prior Art - Idée potentiellement nouvelle")
    print("█" * 70)
    
    idee = """A quantum-based brain wave decoder that uses entangled photons 
    to read neural signals through skin without invasive electrodes, allowing 
    paralyzed patients to control robotic limbs with thoughts."""
    
    result = analyser_invention(idee=idee)
    
    print(f"\n⚖️ VERDICT AUTOMATIQUE : {result['verdict_automatique']['titre']}")
    print(f"   Risque : {result['verdict_automatique']['niveau_risque']}\n")
    print("📋 ANALYSE DU LLM :\n")
    print(result['reponse'])


if __name__ == "__main__":
    print("🧪 LANCEMENT DES TESTS LLM")
    print("=" * 70)

    # test_qa_mode()
    test_qa_avec_filtres()
    test_prior_art_existant()
    test_prior_art_nouvelle()
    
    print("\n\n" + "🎉" * 35)
    print("   TESTS TERMINÉS !")
    print("🎉" * 35)