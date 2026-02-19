import os
import glob
import re
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_text_splitters import MarkdownHeaderTextSplitter

# 1. Charger les variables d'environnement
load_dotenv("../.env")

# 2. Connexion à Neo4j
try:
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password123")
    )
    print("🔌 Connexion à Neo4j réussie !")
except Exception as e:
    print(f"❌ Erreur de connexion Neo4j : {e}")
    exit()



def preparer_texte_nougat(texte):
    """
    Standardise la hiérarchie juridique camerounaise et corrige les erreurs d'OCR
    (titres manquants, texte collé au titre, gras intempestif).
    """
    
    # 1. Nettoyage des scories de l'OCR sur "1er"
    texte = re.sub(r'\\\(.*?\\\)', '1er', texte)
    
    # 2. Standardisation des grands niveaux (Livre, Titre, Chapitre, Section)
    texte = re.sub(r'^(?:#+\s*)?(?:\*\*)*\s*(Livre\s+[IVXLCDM]+.*?)[.\*]*$', r'# \1', texte, flags=re.MULTILINE|re.IGNORECASE)
    texte = re.sub(r'^(?:#+\s*)?(?:\*\*)*\s*(Titre\s+[IVXLCDM]+.*?)[.\*]*$', r'## \1', texte, flags=re.MULTILINE|re.IGNORECASE)
    texte = re.sub(r'^(?:#+\s*)?(?:\*\*)*\s*(Chapitre\s+[IVXLCDM0-9]+.*?)[.\*]*$', r'### \1', texte, flags=re.MULTILINE|re.IGNORECASE)
    texte = re.sub(r'^(?:#+\s*)?(?:\*\*)*\s*(Section\s+[IVXLCDM0-9]+.*?)[.\*]*$', r'#### \1', texte, flags=re.MULTILINE|re.IGNORECASE)
    
    # 3. LA CORRECTION MAGIQUE POUR LES ARTICLES
    # Cette règle fait 3 choses :
    # - Elle détecte "Article X" (qu'il y ait déjà un # ou non, qu'il soit en **gras** ou non)
    # - Elle force le niveau 5 (#####)
    # - S'il y a du texte collé sur la même ligne (ex: "Article 29 : Le texte..."), 
    #   elle capture ce texte (\2) et le rejette à la ligne suivante (\n\2).
    pattern_article = r'^(?:#+\s*)?(?:\*\*)*\s*(Article\s+[0-9]+(?:er|ᵉʳ|ème|[a-zA-Z])?\s*[:\-\.]?)(?:\*\*)*\s*(.*)$'
    texte = re.sub(pattern_article, r'##### \1\n\2', texte, flags=re.MULTILINE|re.IGNORECASE)
    
    return texte
    

def ingest_directory(directory_path):
    # Cherche tous les fichiers .mmd ou .md dans le dossier
    fichiers = glob.glob(os.path.join(directory_path, "*.mmd")) + glob.glob(os.path.join(directory_path, "*.md"))
    
    if not fichiers:
        print(f"⚠️ Aucun fichier trouvé dans {directory_path}")
        return

    print(f"📂 {len(fichiers)} document(s) trouvé(s). Début du traitement en lot...")

    # Configuration du découpeur intelligent de LangChain pour 5 niveaux
    headers_to_split_on = [
        ("#", "Livre"),
        ("##", "Titre"),
        ("###", "Chapitre"),
        ("####", "Section"),
        ("#####", "Article"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    for fichier in fichiers:
        nom_document = os.path.basename(fichier)
        print(f"\n⚙️ Traitement de : {nom_document}")
        
        # Lecture du fichier
        with open(fichier, 'r', encoding='utf-8') as f:
            texte_brut = f.read()

        # Nettoyage avec la nouvelle fonction regex puissante
        texte_propre = preparer_texte_nougat(texte_brut)

        # Découpage sémantique
        chunks = markdown_splitter.split_text(texte_propre)
        print(f"   -> Découpé en {len(chunks)} fragments logiques.")

        # Ingestion dans Neo4j
        for i, chunk in enumerate(chunks):
            contenu = chunk.page_content.strip()
            if not contenu:
                continue # On ignore les fragments vides

            # LangChain place les titres trouvés dans le dictionnaire "metadata"
            metadata = chunk.metadata

            # On définit la hiérarchie possible dans l'ordre de profondeur
            # Si le niveau n'existe pas, il vaudra 'None'
            niveaux_hierarchie = [
                ("Livre", metadata.get("Livre")),
                ("Titre", metadata.get("Titre")),
                ("Chapitre", metadata.get("Chapitre")),
                ("Section", metadata.get("Section")),
                # Par sécurité, si le texte n'a aucun titre, on crée un "Fragment_X"
                ("Article", metadata.get("Article", f"Fragment_{i}")) 
            ]

            # ---------------------------------------------------------
            # CONSTRUCTION DYNAMIQUE DE LA REQUÊTE CYPHER
            # ---------------------------------------------------------
            # On commence toujours par le document racine
            query = "MERGE (doc:DocumentLegal {nom_fichier: $nom_doc})\n"
            params = {"nom_doc": nom_document, "contenu": contenu}
            
            parent_var = "doc" # Le parent actuel est le document

            # On boucle sur les 5 niveaux
            for j, (label, valeur) in enumerate(niveaux_hierarchie):
                if valeur: # Si ce niveau existe dans ce morceau de texte
                    node_var = f"n_{j}"
                    
                    # 1. On crée le nœud (ex: MERGE (n_2:Chapitre {nom: "Chapitre I"}))
                    query += f"MERGE ({node_var}:{label} {{nom: $val_{j}}})\n"
                    
                    # 2. On le relie à son parent direct avec une flèche CONTIENT
                    query += f"MERGE ({parent_var})-[:CONTIENT]->({node_var})\n"
                    
                    # 3. On stocke la valeur pour Neo4j
                    params[f"val_{j}"] = valeur
                    
                    # 4. Ce nœud devient le nouveau parent pour le niveau suivant
                    parent_var = node_var

            # À la fin, on injecte le texte de la loi dans le nœud le plus profond créé
            query += f"SET {parent_var}.contenu = $contenu\n"

            # Exécution dans la base de données
            graph.query(query, params)
            
    print("\n✅ Traitement par lot terminé ! La hiérarchie complexe est rangée dans Neo4j.")

if __name__ == "__main__":
    dossier_cible = "../data_processed"
    ingest_directory(dossier_cible)