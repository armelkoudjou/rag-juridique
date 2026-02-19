import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# NOUVELLES IMPORTATIONS MODERNES (LangChain 0.3+)
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

# 1. Chargement des clés
load_dotenv("../.env")

# 2. Connexion à la base de données Neo4j
print("🔌 Connexion au Graphe Juridique...")
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password123")
)

# 3. Initialisation de l'IA (GPT-4o-mini)
# Température à 0 pour qu'il soit un juriste strict (pas d'hallucination)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 4. Création de la chaîne GraphRAG
# Cette chaîne va lire le schéma de ta base de données toute seule
chain = GraphCypherQAChain.from_llm(
    cypher_llm=llm,       
    qa_llm=llm,           
    graph=graph,          
    verbose=True,         
    allow_dangerous_requests=True 
)

def poser_question(question):
    print(f"\n🧑‍⚖️ Utilisateur : {question}")
    print("🤖 Recherche dans le Droit Camerounais en cours...")
    
    try:
        reponse = chain.invoke({"query": question})
        print(f"\n⚖️ Assistant Juridique :\n{reponse['result']}\n")
    except Exception as e:
        print(f"\n❌ L'IA a rencontré un problème : {e}")

if __name__ == "__main__":
    print("="*50)
    print(" 🏛️ ASSISTANT LEGALTECH CAMEROUN ACTIVÉ ")
    print("="*50)
    print("Tapez 'quitter' pour arrêter le programme.\n")
    
    while True:
        question_utilisateur = input("Posez votre question juridique : ")
        if question_utilisateur.lower() in ['quitter', 'exit', 'q']:
            print("Fermeture de l'assistant. Au revoir !")
            break
            
        poser_question(question_utilisateur)