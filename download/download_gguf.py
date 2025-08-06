# download_gguf.py
import argparse, pathlib
from huggingface_hub import hf_hub_download

p = argparse.ArgumentParser()
p.add_argument("--repo", required=True)
p.add_argument("--file", required=True)
p.add_argument("--out",  required=True)
args = p.parse_args()

dest = pathlib.Path(args.out)
dest.mkdir(parents=True, exist_ok=True)

path = hf_hub_download(
    repo_id=args.repo,
    filename=args.file,
    local_dir=dest,
    resume_download=True,
    local_dir_use_symlinks=False,
)
print("✔ Descargado en:", path)
