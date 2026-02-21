# 🏛️ Assistant Juridique Cameroun - RAG Agent Autonome

**Système juridique intelligent propulsé par GraphRAG, Neo4j et Gemini 2.0 avec auto-correction**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF6B6B?logo=streamlit&logoColor=white)](https://streamlit.io/)

## 🎯 Fonctionnalités

- 🧠 **Agent Juridique Autonome** : Workflow LangGraph avec 3 nœuds (Recherche → Rédaction → Vérification)
- 🔍 **Recherche Hybride** : Vectorielle + Graphe Neo4j pour une précision juridique maximale
- ⚖️ **Self-Correction** : L'IA vérifie automatiquement ses réponses et se corrige
- 🌍 **Multilingue** : Support français/anglais avec embeddings spécialisés
- 📊 **Évaluation RAGAS** : Métriques de qualité automatiques
- 🚀 **API REST** : FastAPI pour intégration web
- 💬 **Interface Streamlit** : Chat interactif avec suivi du raisonnement en temps réel

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF/Docs    │───▶│  OCR + Nougat   │───▶│   Neo4j Graph   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                      │
┌─────────────────┐    ┌──────────────────┐    │              ┌─────────────────┐
│   Questions    │───▶│ Agent LangGraph  │───▶──────────────────▶│  Réponses     │
│   Utilisateurs │    │ (Auto-Correction)│                   │  Validées      │
└─────────────────┘    └──────────────────┘                   └─────────────────┘
```

## 🚀 Démarrage Rapide

### Prérequis

- Python 3.8+
- Docker & Docker Compose
- Clés API (Google Gemini, LlamaParse si besoin)

### 1. Cloner le Repository

```bash
git clone https://github.com/armelkoudjou/rag-juridique.git
cd rag-juridique
```

### 2. Configuration Environnement

```bash
# Créer le fichier .env à la racine
cp .env.example .env

# Éditer avec vos clés
nano .env
```

**Variables requises :**
```env
# Base de données Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Google Gemini (LLM principal)
GOOGLE_API_KEY=votre_clé_gemini

# LlamaParse (optionnel, pour nouveaux PDFs)
LLAMA_CLOUD_API_KEY=votre_clé_llamaparse
```

### 3. Lancer les Services

```bash
# Démarrer Neo4j (base de données graphe)
docker-compose up -d neo4j

# Attendre 30 secondes puis vérifier
# http://localhost:7474  (Interface Neo4j)
```

### 4. Ingestion des Documents

```bash
# Convertir les PDFs en Markdown (si nouveaux documents)
python src/ocr_converter.py

# Ingérer dans Neo4j et vectoriser
python src/ingest_graph.py

# Vectoriser le graphe existant
python src/vectoriser_graphe.py
```

### 5. Lancer les Applications

#### Interface Streamlit (Recommandé)
```bash
streamlit run src/app.py
# Accès : http://localhost:8501
```

#### API REST (Pour développeurs)
```bash
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
# Accès : http://localhost:8000/docs
```

#### Terminal Interactif
```bash
python src/chatbot.py
```

## 📁 Structure du Projet

```
rag-juridique/
├── src/
│   ├── app.py                 # Interface Streamlit avec agent autonome
│   ├── agent_juridique.py     # Cœur de l'agent LangGraph
│   ├── api.py                 # API REST FastAPI
│   ├── chatbot.py            # Terminal interactif
│   ├── ocr_converter.py       # OCR avec Nougat
│   ├── ingest_graph.py        # Ingestion Neo4j
│   ├── vectoriser_graphe.py    # Vectorisation
│   ├── debug_db.py           # Diagnostic base
│   └── evaluation_ragas.py    # Évaluation qualité
├── data/                     # PDFs sources
├── data_processed/           # Markdown convertis
├── docker-compose.yml         # Neo4j container
├── requirements.txt          # Dépendances Python
└── .env                    # Configuration (à créer)
```

## 🔧 Utilisation

### Interface Streamlit

1. **Posez votre question** juridique en français
2. **L'Agent travaille** en 3 étapes visibles :
   - 🔍 Recherche dans le graphe
   - ✍️ Rédaction de la réponse  
   - ⚖️ Vérification auto-correction
3. **Consultez les sources** et métriques de confiance

### API REST

```bash
curl -X POST "http://localhost:8000/api/consultation" \
     -H "Content-Type: application/json" \
     -d '{"question": "Quelle est la peine pour le vol aggravé ?"}'
```

## 🧪 Tests et Évaluation

### Tester l'Agent

```bash
# Test autonome de l'agent
python src/agent_juridique.py

# Évaluation avec RAGAS (nécessite clé Gemini)
python src/evaluation_ragas.py
```

### Débogage Base de Données

```bash
# Vérifier le contenu du graphe
python src/debug_db.py
```

## 📊 Métriques de Performance

L'évaluation RAGAS mesure :
- **Faithfulness** : Fiabilité des citations
- **Answer Relevancy** : Pertinence des réponses
- **Context Precision** : Précision du contexte récupéré
- **Context Recall** : Complétude du contexte

## 🛠️ Technologies Utilisées

- **🧠 LangGraph** : Workflows agentiques autonomes
- **🔍 Neo4j** : Base de données graphe vectorielle
- **🤖 Gemini 2.0** : LLM Google pour raisonnement juridique
- **📚 HuggingFace** : Embeddings multilingues
- **🖼️ Nougat** : OCR avancé pour documents scannés
- **🚀 FastAPI** : API REST haute performance
- **💬 Streamlit** : Interface utilisateur réactive
- **📊 RAGAS** : Évaluation automatique des réponses

## 🤝 Contribution

1. Fork le projet
2. Créer une branche de fonctionnalité (`git checkout -b feature-nouvelle-fonction`)
3. Commiter les changements (`git commit -am 'Ajouter nouvelle fonction'`)
4. Pousser (`git push origin feature-nouvelle-fonction`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour détails.

## 🙏 Remerciements

- **Neo4j** pour la base de données graphe performante
- **Google** pour l'accès à Gemini 2.0
- **LangChain** pour les composants RAG/GraphRAG
- **Meta AI** pour Nougat OCR

---

**🏛️ Assistant Juridique Cameroun** - *L'IA au service du droit camerounais*
