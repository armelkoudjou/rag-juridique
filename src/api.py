import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import de l'agent que vous avez construit
from agent_juridique import assistant_juridique

# Chargement des variables d'environnement (Clés API, Neo4j, etc.)
load_dotenv("../.env")

# Initialisation de l'API
app = FastAPI(
    title="API Assistant Juridique Cameroun & OHADA",
    description="API propulsée par GraphRAG et Gemini",
    version="1.0.0"
)

# 🛡️ Configuration des CORS (Crucial pour le Web)
# Cela autorise votre front-end (qu'il soit en local ou déployé sur des plateformes cloud) à interroger l'API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacez "*" par l'URL exacte de votre site web
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODÈLES DE DONNÉES ---
# Définition du format attendu en entrée (la question du site web)
class RequeteJuridique(BaseModel):
    question: str

# Définition du format de sortie (la réponse renvoyée au site web)
class ReponseJuridique(BaseModel):
    reponse: str
    sources: str

# --- ROUTES DE L'API ---
@app.get("/")
def read_root():
    return {"message": "L'API Juridique est en ligne !"}

@app.post("/api/consultation", response_model=ReponseJuridique)
async def consulter_agent(requete: RequeteJuridique):
    print(f"📥 Nouvelle question reçue : {requete.question}")
    
    try:
        # Exécution de l'agent LangGraph de manière asynchrone
        output = assistant_juridique.invoke({"question": requete.question})
        
        # Formatage de la réponse pour le site web
        return ReponseJuridique(
            reponse=output.get("reponse_brouillon", "Désolé, aucune réponse générée."),
            sources=output.get("contexte", "Aucune source extraite.")
        )
        
    except Exception as e:
        print(f"❌ Erreur API : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne de l'agent IA.")