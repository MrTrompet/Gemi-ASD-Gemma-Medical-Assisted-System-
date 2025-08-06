# download_gemma.py
from pathlib import Path
from huggingface_hub import snapshot_download

# Import robusto para distintas versiones de huggingface_hub
try:
    from huggingface_hub.utils import HfHubHTTPError
except ImportError:
    from huggingface_hub.errors import HfHubHTTPError  # fallback

REPO_ID = "google/gemma-3n-E2B-it-litert-preview"
TARGET_DIR = Path("models/gemma3n")
PATTERNS = ["*.tflite", "*.task", "*.json", "*.model", "*.spm", "tokenizer*", "*.txt"]

def print_tree(root: Path, prefix: str = ""):
    entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    for i, p in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(prefix + connector + p.name)
        if p.is_dir():
            ext = "    " if i == len(entries) - 1 else "│   "
            print_tree(p, prefix + ext)

def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Descargando {REPO_ID} -> {TARGET_DIR.resolve()}")
    try:
        snapshot_download(
            repo_id=REPO_ID,
            local_dir=str(TARGET_DIR),
            local_dir_use_symlinks=False,
            allow_patterns=PATTERNS,
        )
    except HfHubHTTPError as e:
        print("\n¡Error al descargar!\n", e)
        print("\nPosibles causas:")
        print("  - No aceptaste los términos en la página del modelo.")
        print("  - El token no tiene permisos (revisa `hf auth whoami`).")
        print("  - Problemas de red/firewall.")
        return
    except Exception as e:
        print("\nFallo inesperado:\n", repr(e))
        return

    print("\nDescarga completada.")
    print_tree(TARGET_DIR)

if __name__ == "__main__":
    main()
