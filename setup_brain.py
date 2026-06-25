import os
from sentence_transformers import SentenceTransformer
from pathlib import Path
import shutil

def setup():
    # 1. Define the target structure
    # We want: ./brain/embeddings/all-MiniLM-L6-v2/
    base_path = Path("./brain/embeddings/all-MiniLM-L6-v2")
    model_name = "all-MiniLM-L6-v2"

    print(f"--- CODER BRAIN INITIALIZATION ---")
    
    # 2. Create directories
    if not base_path.exists():
        print(f"[+] Creating directory: {base_path}")
        base_path.mkdir(parents=True, exist_ok=True)
    else:
        print(f"[!] Directory {base_path} already exists. Skipping creation.")

    # 3. Download the model
    # This will download to your system cache first to ensure integrity
    print(f"[+] Downloading {model_name} from HuggingFace (this may take a minute)...")
    try:
        model = SentenceTransformer(model_name)
        
        # 4. Save the model into our specific 'brain' folder
        print(f"[+] Exporting model to local brain folder...")
        model.save(str(base_path))
        
        print(f"\n[SUCCESS] BRAIN IS ONLINE.")
        print(f"Location: {base_path.absolute()}")
        print(f"You can now run CODER.py offline.")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to setup brain: {e}")
        print("Ensure you have an internet connection for this setup step.")

if __name__ == "__main__":
    setup()