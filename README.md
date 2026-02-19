🇨🇲 LegalTech Cameroun - Assistant Juridique GraphRAG
Ce projet est un assistant juridique intelligent basé sur le Droit Camerounais. Il utilise un pipeline d'ingestion OCR (LlamaParse), une base de données orientée graphe (Neo4j) et un modèle de langage (OpenAI) pour fournir des réponses précises et sourcées (GraphRAG).

🛠️ Prérequis
Avant de commencer, assurez-vous d'avoir installé sur votre machine :

Git (pour cloner le projet)

Docker Desktop (pour faire tourner la base de données Neo4j localement)

Miniconda ou Anaconda (fortement recommandé pour la gestion de l'environnement Python)

🚀 Étape 1 : Installation et Configuration
1. Cloner le dépôt

Bash
git clone https://github.com/TON_NOM_UTILISATEUR/TON_DEPOT.git
cd TON_DEPOT
2. Créer et activer l'environnement virtuel (Python 3.10 recommandé)

Bash
conda create -n legaltech-env python=3.10 -y
conda activate legaltech-env
3. Installer les dépendances
(Note pour l'équipe : si vous n'avez pas créé de fichier requirements.txt, dites à vos collaborateurs de lancer cette commande) :

Bash
pip install langchain langchain-community langchain-openai langchain-neo4j python-dotenv llama-parse
🔐 Étape 2 : Variables d'Environnement (TRÈS IMPORTANT)
⚠️ Ne poussez jamais vos clés API sur GitHub !

À la racine du projet, créez un fichier nommé exactement .env (il sera ignoré par Git si vous avez bien configuré votre .gitignore).

Copiez-collez ce modèle à l'intérieur et remplissez-le avec vos propres clés :

Plaintext
# --- Base de données Neo4j (Locale via Docker) ---
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# --- API Keys pour l'Intelligence Artificielle ---
# Clé LlamaCloud (Pour l'OCR des PDF) : https://cloud.llamaindex.ai/
LLAMA_CLOUD_API_KEY=llx-votre_cle_ici

# Clé OpenAI (Pour le Chatbot) : https://platform.openai.com/
OPENAI_API_KEY=sk-votre_cle_ici
🗄️ Étape 3 : Lancement de la Base de Données
Assurez-vous que Docker Desktop est ouvert, puis lancez le conteneur Neo4j en arrière-plan :

Bash
docker compose up -d
Vous pouvez vérifier que la base est allumée en allant sur http://localhost:7474 dans votre navigateur (Identifiant : neo4j / Mot de passe : password123).

🏃‍♂️ Étape 4 : Le Workflow (Comment utiliser l'application)
L'application fonctionne en 3 étapes distinctes, situées dans le dossier src/.

Phase A : Extraction (OCR)
Placez vos documents juridiques au format PDF dans le dossier data_raw/, puis lancez :

Bash
cd src
python ocr_converter.py
Résultat : LlamaParse va lire les PDF, nettoyer les tampons officiels, et générer des fichiers Markdown propres dans le dossier data_processed/.

Phase B : Ingestion et Structuration (GraphRAG)
Pour découper les lois en Articles/Chapitres et les ranger dans Neo4j :

Bash
python ingest_graph_v2.py
Résultat : Allez sur http://localhost:7474, tapez MATCH (n) RETURN n et admirez le graphe juridique !

Phase C : Le Chatbot
Pour lancer l'assistant conversationnel et interroger la base de données :

Bash
python chatbot.py
Posez votre question en langage naturel, l'IA cherchera les articles de loi pertinents dans le graphe et vous répondra.
