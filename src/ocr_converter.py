import os
import glob
from dotenv import load_dotenv
from llama_parse import LlamaParse

# 1. Charger les clés secrètes
load_dotenv("../.env")

def convert_all_pdfs_with_llamaparse(input_dir, output_dir):
    pdfs = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdfs:
        print(f"❌ Aucun fichier PDF trouvé dans {input_dir}")
        return

    print(f"📂 {len(pdfs)} PDF trouvé(s). Connexion au Cloud LlamaParse...")

    # 2. Configurer l'Intelligence Artificielle
    parser = LlamaParse(
        api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
        result_type="markdown",  # On veut du Markdown propre
        language="fr",           # On force le français pour éviter les erreurs sur les accents
        verbose=True
    )

    # 3. Traiter chaque fichier
    for pdf_path in pdfs:
        nom_fichier = os.path.basename(pdf_path)
        nom_sans_extension = os.path.splitext(nom_fichier)[0]
        fichier_sortie = os.path.join(output_dir, f"{nom_sans_extension}.md")
        
        print(f"\n🚀 Envoi de '{nom_fichier}' dans le Cloud (ça peut prendre quelques minutes pour les gros livres)...")
        
        try:
            # LlamaParse lit le document et renvoie une liste de pages
            documents = parser.load_data(pdf_path)
            
            # On colle toutes les pages ensemble
            texte_complet = "\n\n".join([doc.text for doc in documents])
            
            # On sauvegarde le résultat dans le dossier data_processed
            with open(fichier_sortie, 'w', encoding='utf-8') as f:
                f.write(texte_complet)
                
            print(f"✅ Conversion réussie ! Fichier sauvegardé sous : {fichier_sortie}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la conversion de {nom_fichier} : {e}")

if __name__ == "__main__":
    dossier_entree = "../data_raw"
    dossier_sortie = "../data_processed"
    
    os.makedirs(dossier_entree, exist_ok=True)
    os.makedirs(dossier_sortie, exist_ok=True)
    
    convert_all_pdfs_with_llamaparse(dossier_entree, dossier_sortie)