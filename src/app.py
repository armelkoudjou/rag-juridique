import os
from typing import TypedDict
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

# --- 1. CONFIGURATION DE LA PAGE STREAMLIT ---
st.set_page_config(page_title="LegalTech Cameroun", page_icon="⚖️", layout="centered")

# --- 2. DÉFINITION DE L'ÉTAT DE L'AGENT (Sa mémoire) ---
class AgentState(TypedDict):
    question: str
    question_propre: str
    contexte: str
    sources_brutes: list
    reponse_brouillon: str
    feedback: str
    est_valide: bool
    compteur_revisions: int

# --- 3. INITIALISATION DU MOTEUR (Mise en cache) ---
@st.cache_resource
def init_agent():
    load_dotenv("../.env")
    
    # A. Modèles (Vecteurs et LLM)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0
)
    
    # B. Connexion Neo4j
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
    retriever = vector_store.as_retriever(search_kwargs={'k': 2})

    # C. Définition des Noeuds du Graphe
    def node_recherche(state: AgentState):
        """Reformule la question et extrait les articles de Neo4j."""
        question = state["question"]
    
        # Reformulation
        correcteur_prompt = PromptTemplate.from_template(
            "Corrige l'orthographe de cette question juridique. Renvoie UNIQUEMENT la question corrigée : {question}"
        )
        question_propre = (correcteur_prompt | llm | StrOutputParser()).invoke({"question": question})
        
        # Extraction Neo4j
        docs = retriever.invoke(question_propre)
        textes_uniques = []
        titres_vus = set()
        sources_brutes = []
        
        for doc in docs:
            titre = doc.metadata.get('titre')
            chapitre = doc.metadata.get('chapitre', 'Chapitre inconnu')
            if titre not in titres_vus:
                titres_vus.add(titre)
                textes_uniques.append(doc.page_content)
                sources_brutes.append(f"**{chapitre}** > {titre}")
                
        return {
            "question_propre": question_propre, 
            "contexte": "\n\n".join(textes_uniques), 
            "sources_brutes": sources_brutes,
            "compteur_revisions": 0
        }

    def node_redacteur(state: AgentState):
        """Rédige la réponse en se basant sur la loi et les éventuelles corrections."""
        template = """Tu es un brillant avocat camerounais.
        RÈGLES ABSOLUES :
        1. Utilise UNIQUEMENT les textes de loi ci-dessous.
        2. Fais le calcul mathématique exact si un article modifie une peine (ex: "les peines sont doublées").
        3. Ajoute une section "📚 Références Juridiques" à la fin.
        
        Textes de loi :
        {contexte}
        
        Question : {question_propre}
        Remarque du Juge Vérificateur (corrige ton texte en fonction) : {feedback}
        
        Réponse détaillée :"""
        
        chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
        reponse = chain.invoke({
            "contexte": state["contexte"], 
            "question_propre": state["question_propre"],
            "feedback": state.get("feedback", "Aucune remarque.")
        })
        return {"reponse_brouillon": reponse, "compteur_revisions": state.get("compteur_revisions", 0) + 1}

    def node_verificateur(state: AgentState):
        """Vérifie mathématiquement et juridiquement le brouillon."""
        template = """Tu es un Juge de Paix intraitable. Vérifie la réponse de l'avocat face à la loi.
        Loi : {contexte}
        Réponse : {reponse_brouillon}
        
        Vérifie :
        1. L'avocat a-t-il inventé une information ?
        2. Les calculs de peines (ex: peines doublées) sont-ils mathématiquement exacts ?
        
        Si TOUT est parfait, réponds EXACTEMENT : VALIDE
        Sinon, réponds INVALIDE suivi de l'erreur à corriger."""
        
        evaluation = (PromptTemplate.from_template(template) | llm | StrOutputParser()).invoke({
            "contexte": state["contexte"], 
            "reponse_brouillon": state["reponse_brouillon"]
        })
        
        est_valide = evaluation.strip().startswith("VALIDE")
        return {"est_valide": est_valide, "feedback": evaluation}

    def decider_suite(state: AgentState):
        """Routeur : décide si on boucle ou si on s'arrête."""
        if state["est_valide"] or state["compteur_revisions"] >= 1:
            return "fin"
        return "reviser"

    # D. Construction et Compilation du Graphe
    workflow = StateGraph(AgentState)
    workflow.add_node("recherche", node_recherche)
    workflow.add_node("redacteur", node_redacteur)
    workflow.add_node("verificateur", node_verificateur)
    
    workflow.set_entry_point("recherche")
    workflow.add_edge("recherche", "redacteur")
    workflow.add_edge("redacteur", "verificateur")
    workflow.add_conditional_edges("verificateur", decider_suite, {"reviser": "redacteur", "fin": END})
    
    return workflow.compile()

# Démarrage de l'agent
agent_autonome = init_agent()

# --- 4. DESIGN DE L'INTERFACE UTILISATEUR ---
st.title("🏛️ Assistant Juridique Autonome")
st.markdown("*Posez vos questions sur le Droit Camerounais. L'Agent IA va rechercher, rédiger, et s'auto-corriger avant de vous répondre.*")
st.divider()

# --- 5. GESTION DE L'HISTORIQUE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. LOGIQUE DE CHAT AVEC FLUX LANGGRAPH ---
if question := st.chat_input("Ex: Quelle est la peine pour le vol aggravé avec arme ?"):
    
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
        
    with st.chat_message("assistant"):
        status_container = st.status("L'Agent traite votre demande...", expanded=True)
        
        try:
            # On crée des variables pour stocker les infos au fur et à mesure
            reponse_finale = ""
            sources = []
            question_propre = ""
            
            # On lance le graphe UNE SEULE FOIS
            for output in agent_autonome.stream({"question": question}):
                for node_name, state_update in output.items():
                    
                    # On capture les données vitales dès qu'elles apparaissent dans le graphe
                    if "reponse_brouillon" in state_update:
                        reponse_finale = state_update["reponse_brouillon"]
                    if "sources_brutes" in state_update:
                        sources = state_update["sources_brutes"]
                    if "question_propre" in state_update:
                        question_propre = state_update["question_propre"]
                    
                    # Mise à jour de l'interface visuelle
                    if node_name == "recherche":
                        status_container.write("✅ **Recherche terminée :** Articles extraits du Graphe Neo4j.")
                    elif node_name == "redacteur":
                        status_container.write(f"✍️ **Rédaction en cours :** Brouillon n°{state_update.get('compteur_revisions', 1)} généré.")
                    elif node_name == "verificateur":
                        if state_update["est_valide"]:
                            status_container.write("⚖️ **Validation (Juge de Paix) :** Réponse conforme à la loi !")
                        else:
                            status_container.write("⚠️ **Correction nécessaire :** Le Juge a détecté une erreur, retour à la rédaction...")

            status_container.update(label="Analyse terminée !", state="complete", expanded=False)
            
            # Affichage de la réponse même si le Juge n'était pas content au 3ème essai
            if reponse_finale:
                st.markdown(reponse_finale)
                
                with st.expander("🔍 Voir les coulisses (Articles extraits)"):
                    st.info(f"Question reformulée : *{question_propre}*")
                    for source in sources:
                        st.caption(f"- {source}")
                        
                st.session_state.messages.append({"role": "assistant", "content": reponse_finale})
            else:
                st.warning("L'agent n'a pas pu formuler de réponse.")
            
        except Exception as e:
            status_container.update(label="Une erreur est survenue", state="error")
            st.error(f"Détail de l'erreur : {e}")