import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Charger les mots de passe
load_dotenv("../.env")

print("⏳ Chargement du modèle d'Embeddings (Français)...")
# On utilise un modèle multilingue très performant pour le droit
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print("🔌 Connexion à Neo4j et création de l'Index Vectoriel...")
print("⚙️ (Cela peut prendre quelques minutes, l'IA lit et vectorise chaque article...)")

# 2. La Magie : On vectorise la base existante !
vector_index = Neo4jVector.from_existing_graph(
    embedding=embeddings,
    url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password123"),
    index_name="article_vector_index", # Le nom de notre moteur de recherche sémantique
    node_label="Article",              # On vectorise les bulles Article
    text_node_properties=["nom", "contenu"], # On mélange le titre et le texte pour le sens
    embedding_node_property="embedding" # On sauvegarde le vecteur ici
)

print("\n✅ VECTORISATION TERMINÉE ! Ton Graphe est devenu Sémantique.")