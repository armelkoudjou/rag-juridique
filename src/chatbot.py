import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Chargement des clés
load_dotenv("../.env")

print("🔌 Connexion au Graphe Sémantique...")

# 2. Le Cerveau Sémantique (HuggingFace)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# 3. Le Moteur de Recherche Hybride (Vecteur + Graphe)
requete_hybride = """
MATCH (parent)-[:CONTIENT]->(node)
MATCH (parent)-[:CONTIENT]->(voisin:Article)
RETURN voisin.nom + ' : ' + coalesce(voisin.contenu, '') AS text, score, {titre: voisin.nom, chapitre: parent.nom} AS metadata
"""

vector_store = Neo4jVector.from_existing_index(
    embedding=embeddings,
    url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password123"),
    index_name="article_vector_index",
    retrieval_query=requete_hybride
)

# On demande à Neo4j de trouver le meilleur concept (k=1) et d'aspirer ses voisins
retriever = vector_store.as_retriever(search_kwargs={'k': 5})

# 4. L'IA Avocat (Llama 3.3)
llm = ChatGroq(model="gemini-2.0-flash-001", temperature=0)

# 5. Le Prompt de l'Avocat
template = """Tu es un brillant avocat camerounais.
Utilise le contexte juridique ci-dessous (qui contient l'article pertinent et tout son chapitre) pour répondre à la question de ton client.

RÈGLE ABSOLUE : Si un article (ex: vol aggravé) fait référence à un AUTRE article pour la peine de base (ex: "les peines de l'article X sont doublées"), cherche cet article de base dans le contexte, extrais les montants (francs) et durées (années), et FAIS LE CALCUL MATHÉMATIQUE EXACT pour le client.

Contexte extrait de la base :
{context}

Question du client : {question}
Réponse détaillée et structurée de l'avocat :"""

QA_PROMPT = PromptTemplate.from_template(template)

def poser_question(question):
    print(f"\n🧑‍⚖️ Utilisateur : {question}")
    print("🤖 Recherche sémantique et exploration du Graphe en cours...")
    
    try:
        # ÉTAPE A : Le Retriever fouille le Graphe et ramène les textes (top 5)
        docs = retriever.invoke(question)
        
        # DÉDUPLICATION : On nettoie les doublons au cas où plusieurs articles du même chapitre remontent
        textes_uniques = []
        titres_vus_pour_dedup = set()
        for doc in docs:
            titre = doc.metadata.get('titre')
            if titre not in titres_vus_pour_dedup:
                titres_vus_pour_dedup.add(titre)
                textes_uniques.append(doc.page_content)
                
        contexte_texte = "\n\n".join(textes_uniques)

        # ÉTAPE B : La chaîne LCEL (L'IA réfléchit sur le contexte nettoyé)
        chain = QA_PROMPT | llm | StrOutputParser()
        reponse = chain.invoke({"context": contexte_texte, "question": question})
        
        print(f"\n⚖️ Assistant Juridique :\n{reponse}\n")
        
        # ÉTAPE C : Affichage transparent des sources trouvées
        print("-" * 40)
        print("📚 Chapitres scannés par l'IA :")
        chapitres_vus = set()
        for doc in docs:
            chapitre = doc.metadata.get('chapitre', 'Chapitre inconnu')
            if chapitre not in chapitres_vus:
                print(f"- {chapitre}")
                chapitres_vus.add(chapitre)
                    
    except Exception as e:
        print(f"\n❌ L'IA a rencontré un problème : {e}")

if __name__ == "__main__":
    print("="*50)
    print(" 🏛️ ASSISTANT HYBRIDE LEGALTECH ACTIVÉ ")
    print("="*50)
    print("Tapez 'quitter' pour arrêter le programme.\n")
    
    while True:
        question_utilisateur = input("Posez votre question juridique : ")
        if question_utilisateur.lower() in ['quitter', 'exit', 'q']:
            print("Fermeture de l'assistant. Au revoir !")
            break
            
        poser_question(question_utilisateur)