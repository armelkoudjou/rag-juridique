import os
from typing import TypedDict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END



# --- 1. CONFIGURATION INITIALE ---
load_dotenv("../.env")

# Initialisation des modèles
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

# Requête hybride Neo4j (identique à votre implémentation)
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
retriever = vector_store.as_retriever(search_kwargs={'k': 1})


# --- 2. DÉFINITION DE L'ÉTAT DU GRAPHE (La Mémoire de l'Agent) ---
class AgentState(TypedDict):
    question: str
    question_propre: str
    contexte: str
    reponse_brouillon: str
    feedback: str
    est_valide: bool
    compteur_revisions: int


# --- 3. DÉFINITION DES NOEUDS (Les "Travailleurs") ---

def node_recherche(state: AgentState):
    """Corrige la question et fouille le graphe Neo4j."""
    print("🔍 [Nœud 1] Recherche dans le graphe...")
    question = state["question"]
    
    # Reformulation silencieuse
    correcteur_prompt = PromptTemplate.from_template(
        "Corrige les fautes d'orthographe de cette question juridique pour qu'elle soit parfaite. "
        "Ne réponds pas à la question, renvoie JUSTE la question corrigée : {question}"
    )
    question_propre = (correcteur_prompt | llm | StrOutputParser()).invoke({"question": question})
    
    # Recherche Neo4j
    docs = retriever.invoke(question_propre)
    textes_uniques = []
    titres_vus = set()
    for doc in docs:
        titre = doc.metadata.get('titre')
        if titre not in titres_vus:
            titres_vus.add(titre)
            textes_uniques.append(doc.page_content)
    
    contexte = "\n\n".join(textes_uniques)
    
    return {"question_propre": question_propre, "contexte": contexte, "compteur_revisions": 0}


def node_redacteur(state: AgentState):
    """L'Avocat rédige le brouillon de la réponse."""
    print("✍️ [Nœud 2] Rédaction de l'avis juridique...")
    
    template = """Tu es un brillant avocat camerounais.
    RÈGLES ABSOLUES :
    1. Utilise UNIQUEMENT les textes de loi ci-dessous.
    2. Fais les calculs mathématiques exacts si les peines sont modifiées (ex: doublées).
    3. Cite tes sources à la fin.
    
    Contexte :
    {contexte}
    
    Question : {question_propre}
    
    Remarque du vérificateur (si applicable) : {feedback}
    
    Réponse détaillée :"""
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    reponse = chain.invoke({
        "contexte": state["contexte"], 
        "question_propre": state["question_propre"],
        "feedback": state.get("feedback", "Aucune remarque, c'est ton premier jet.")
    })
    
    return {"reponse_brouillon": reponse, "compteur_revisions": state["compteur_revisions"] + 1}


def node_verificateur(state: AgentState):
    """Le Juge de Paix vérifie s'il y a des hallucinations ou erreurs de calcul."""
    print("⚖️ [Nœud 3] Vérification stricte (Self-Correction)...")
    
    template = """Tu es un Réviseur Juridique (Juge de Paix) implacable.
    Vérifie la réponse de l'avocat par rapport aux textes de loi stricts.
    
    Loi :
    {contexte}
    
    Réponse de l'avocat :
    {reponse_brouillon}
    
    INSTRUCTIONS :
    1. L'avocat a-t-il inventé un article, une peine, ou extrapolé ?
    2. Les calculs de peines (si doublées, etc.) sont-ils mathématiquement exacts ?
    
    Si TOUT est parfaitement exact et basé sur la loi, réponds EXACTEMENT et UNIQUEMENT le mot : VALIDE
    S'il y a la MOINDRE erreur, réponds INVALIDE suivi de l'explication de l'erreur pour que l'avocat la corrige.
    """
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    evaluation = chain.invoke({
        "contexte": state["contexte"], 
        "reponse_brouillon": state["reponse_brouillon"]
    })
    
    if evaluation.strip().startswith("VALIDE"):
        print("✅ Vérification réussie : Aucun problème juridique détecté.")
        return {"est_valide": True, "feedback": ""}
    else:
        print(f"❌ Erreur détectée par l'IA : {evaluation}")
        return {"est_valide": False, "feedback": evaluation}


# --- 4. ROUTAGE CONDITIONNEL ---
def decider_suite(state: AgentState):
    """Décide s'il faut renvoyer le texte à l'avocat ou terminer."""
    if state["est_valide"]:
        return "fin"
    if state["compteur_revisions"] >= 3:
        print("⚠️ Nombre maximum de révisions atteint. Arrêt forcé.")
        return "fin"
    return "reviser"


# --- 5. CONSTRUCTION DU GRAPHE ---
workflow = StateGraph(AgentState)

# Ajout des noeuds
workflow.add_node("recherche", node_recherche)
workflow.add_node("redacteur", node_redacteur)
workflow.add_node("verificateur", node_verificateur)

# Définition du flux
workflow.set_entry_point("recherche")
workflow.add_edge("recherche", "redacteur")
workflow.add_edge("redacteur", "verificateur")

# Ajout de la boucle conditionnelle
workflow.add_conditional_edges(
    "verificateur",
    decider_suite,
    {
        "reviser": "redacteur", # Retour à la rédaction si invalide
        "fin": END              # Fin du processus si valide
    }
)

# Compilation de l'agent
assistant_juridique = workflow.compile()


# --- 6. TEST DE L'AGENT ---
if __name__ == "__main__":
    print("="*50)
    print(" 🏛️ AGENT AUTONOME LEGALTECH (LangGraph) ACTIVÉ ")
    print("="*50)
    
    question_test = "Quelle est la peine pour un vol aggravé avec port d'arme selon le code pénal ?"
    print(f"Utilisateur : {question_test}\n")
    
    # Lancement du graphe
    resultat = assistant_juridique.invoke({"question": question_test, "compteur_revisions": 0})
    
    print("\n" + "="*50)
    print(" 📜 RÉPONSE FINALE VALIDÉE :")
    print("="*50)
    print(resultat["reponse_brouillon"])