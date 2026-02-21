import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

# Chargement des clés
load_dotenv("../.env")

print("🔌 Connexion à la base de données Neo4j...")
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password123")
)

print("\n" + "="*40)
print(" 🛠️ DIAGNOSTIC DU GRAPHE JURIDIQUE")
print("="*40)

# 1. Compter tout ce qui existe
res_total = graph.query("MATCH (n) RETURN count(n) AS total")
print(f"Total de bulles (noeuds) dans le graphe : {res_total[0]['total']}")

# 2. Vérifier si la propriété s'appelle bien "contenu"
res_contenu = graph.query("MATCH (n) WHERE n.contenu IS NOT NULL RETURN count(n) AS total")
print(f"Bulles contenant du texte de loi : {res_contenu[0]['total']}")

# 3. Vérifier la présence des mots clés
res_vol = graph.query("MATCH (n) WHERE toLower(n.contenu) CONTAINS 'vol' RETURN count(n) AS total")
print(f"Bulles contenant le mot 'vol' : {res_vol[0]['total']}")

res_arme = graph.query("MATCH (n) WHERE toLower(n.contenu) CONTAINS 'arme' RETURN count(n) AS total")
print(f"Bulles contenant le mot 'arme' : {res_arme[0]['total']}")

# 4. Afficher un exemple concret pour voir à quoi ça ressemble
if res_contenu[0]['total'] > 0:
    print("\n--- EXEMPLE D'UN TEXTE SAUVEGARDÉ DANS LA BASE ---")
    sample = graph.query("MATCH (n) WHERE n.contenu IS NOT NULL RETURN labels(n)[0] AS Label, n.nom AS Titre, substring(n.contenu, 0, 150) AS texte LIMIT 1")
    print(f"Label (Type) : {sample[0]['Label']}")
    print(f"Titre : {sample[0]['Titre']}")
    print(f"Texte (début) : {sample[0]['texte']}...")