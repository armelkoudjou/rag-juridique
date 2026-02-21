import os
import time
import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv

# 1. Charger l'environnement AVANT d'importer l'agent
load_dotenv("../.env") 

# 2. Imports Ragas et Google
from ragas import evaluate
from ragas.metrics.collections import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_google_genai import ChatGoogleGenerativeAI

# 3. Import de l'agent
from agent_juridique import assistant_juridique

# Configuration du Juge (Gemini)
juge_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

# --- LE GOLD DATASET (Réduit à 2 questions pour passer les quotas) ---
test_data = [
    {
        "question": "Quelle est la peine pour un vol aggravé avec port d'arme ?",
        "ground_truth": "La peine est un emprisonnement de 10 à 20 ans (doublement de la peine de l'article 318 selon l'article 320 du Code Pénal)."
    },
    {
        "question": "Quels sont les principes de la protection du consommateur au Cameroun ?",
        "ground_truth": "Les principes incluent la protection de la vie, la satisfaction des besoins essentiels, l'équité et le droit de participation (Article 3 Loi 2011/012)."
    }
]

def executer_evaluation():
    results = []
    print("🚀 Début de l'évaluation 'Tout Gemini' (avec gestion stricte des quotas)...")
    
    for i, item in enumerate(test_data):
        print(f"\n⏳ Attente de 15 secondes avant le test {i+1} pour respecter les quotas API...")
        time.sleep(15) # Pause cruciale pour éviter l'erreur 429 RPM
        
        print(f"🔍 Analyse de : {item['question']}")
        try:
            # L'agent tourne sur Gemini
            output = assistant_juridique.invoke({"question": item["question"]})
            
            results.append({
                "question": item["question"],
                "answer": output["reponse_brouillon"],
                "contexts": [output["contexte"]],
                "ground_truth": item["ground_truth"]
            })
            print("✅ Réponse générée avec succès.")
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération pour ce test : {e}")
            print("⏭️ On passe au test suivant.")

    if not results:
        print("❌ Aucune donnée n'a pu être générée. Arrêt de l'évaluation.")
        return

    dataset = Dataset.from_list(results)
    
    print("\n⚖️ Calcul des scores RAGAS en cours...")
    print("⏳ Cela peut prendre du temps car RAGAS fait plusieurs requêtes à l'API...")
    
    try:
        # Évaluation RAGAS
        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=juge_llm
        )
        
        df = result.to_pandas()
        print("\n🏆 SCORES MOYENS DU SYSTÈME :")
        print(result)
        
        df.to_csv("src/resultats_ragas_gemini_final.csv", index=False)
        print("\n💾 Sauvegardé dans 'src/resultats_ragas_gemini_final.csv'")
        
    except Exception as e:
         print(f"\n❌ Erreur fatale lors du calcul RAGAS : {e}")

if __name__ == "__main__":
    executer_evaluation()