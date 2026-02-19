# 🇨🇲 LegalTech Cameroun - Assistant Juridique GraphRAG

Ce projet est un assistant juridique intelligent basé sur le **Droit Camerounais**.  
Il combine :
- 📝 **OCR (LlamaParse)** pour extraire le texte des documents juridiques (PDF).  
- 🗃️ **Neo4j** comme base de données orientée graphe.  
- 🤖 **OpenAI** pour l’analyse et la génération de réponses précises et sourcées via **GraphRAG**.

---

## 🛠️ Prérequis

Avant de commencer, assurez-vous d’avoir installé :

- **Git** (pour cloner le projet)  
- **Docker Desktop** (pour faire tourner Neo4j localement)  
- **Miniconda ou Anaconda** (fortement recommandé pour gérer l’environnement Python)

---

## 🚀 Étape 1 : Installation et Configuration

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/TON_NOM_UTILISATEUR/TON_DEPOT.git
   cd TON_DEPOT
2. Créer et activer l’environnement virtuel (Python 3.10 recommandé)
  conda create -n legaltech-env python=3.10 -y
  conda activate legaltech-env
3. Installer les dépendances
   pip install langchain langchain-community langchain-openai langchain-neo4j python-dotenv llama-parse

## 🔐Étape 2 : Variables d’Environnement (TRÈS IMPORTANT)
Ne poussez jamais vos clés API sur GitHub !

À la racine du projet, créez un fichier .env et ajoutez vos clés :

# --- Base de données Neo4j (Locale via Docker) ---
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# --- API Keys pour l'Intelligence Artificielle ---
# Clé LlamaCloud (OCR des PDF) : https://cloud.llamaindex.ai/
LLAMA_CLOUD_API_KEY=llx-votre_cle_ici

# Clé OpenAI (Chatbot) : https://platform.openai.com/
OPENAI_API_KEY=sk-votre_cle_ici

## 🗄️ Étape 3 : Lancement de la Base de Données
Assurez-vous que Docker Desktop est ouvert, puis lancez Neo4j :
docker compose up -d
érifiez l’accès via http://localhost:7474  
Identifiant : neo4j / Mot de passe : password123

##🏃‍♂️ Étape 4 : Workflow (Utilisation de l’Application)
L’application fonctionne en 3 phases, situées dans le dossier src/.

Phase A : Extraction (OCR)
Placez vos PDF juridiques dans data_raw/, puis lancez :
cd src python ocr_converter.py

👉 Résultat : fichiers Markdown propres dans data_processed/.

#Phase B : Ingestion et Structuration (GraphRAG)
Découper les lois en Articles/Chapitres et les insérer dans Neo4j :
python ingest_graph_v2.py
👉 Vérifiez dans Neo4j avec :
MATCH (n) RETURN n


Phase C : Chatbot
Lancer l’assistant conversationnel :

python chatbot.py

👉 Posez vos questions en langage naturel, l’IA cherchera les articles pertinents et vous répondra.

📌 Notes Importantes
Pensez à surveiller votre quota OpenAI (erreur 429 = quota dépassé).

Utilisez un cache local pour éviter de réinterroger inutilement l’API.

Les clés API doivent rester privées et sécurisées.

🎯 Objectif
Ce projet vise à démocratiser l’accès au droit Camerounais grâce à l’IA et aux graphes de connaissances.
