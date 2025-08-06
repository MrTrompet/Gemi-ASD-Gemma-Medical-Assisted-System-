#!/usr/bin/env python
# download_unsloth.py
# -------------------
# Descarga (o reanuda) un GGUF desde HuggingFace Hub.
# • Si existe $HF_TOKEN lo usa; si no, lo pide por consola.

import argparse
import getpass
import os
import pathlib
import sys
from huggingface_hub import hf_hub_download, login


def ensure_token() -> None:
    """Garantiza que $HF_TOKEN esté presente para la sesión actual."""
    if os.getenv("HF_TOKEN"):
        return                        # ya existe

    print("⚠  No se encontró $HF_TOKEN.")
    token = getpass.getpass("Pega tu token HF (no se mostrará): ").strip()
    if not token:
        sys.exit("✖  Se requiere un token HF para continuar.")
    login(token=token, add_to_git_credential=False)
    os.environ["HF_TOKEN"] = token   # visible para hf_hub_download


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Descarga un modelo GGUF con reanudación."
    )
    ap.add_argument("--repo", required=True,
                    help="Repo HF (ej. unsloth/gemma-3n-E2B-it-GGUF)")
    ap.add_argument("--file", required=True,
                    help="Nombre de archivo (ej. gemma-3n-E2B-it-Q4_K_M.gguf)")
    ap.add_argument("--out", required=True,
                    help="Carpeta destino (se crea si no existe)")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    ensure_token()

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"→ Descargando {args.repo}/{args.file}")
    print(f"  → Carpeta destino: {out_dir.resolve()}")

    try:
        path = hf_hub_download(
            repo_id=args.repo,
            filename=args.file,
            local_dir=out_dir,
            resume_download=True,
            local_dir_use_symlinks=False,
        )
    except Exception as e:            # HfHubDownloadError u otros
        sys.exit(f"✖  Error al descargar: {e}")

    print(f"✓ Descargado en: {path}")


if __name__ == "__main__":
    main()
