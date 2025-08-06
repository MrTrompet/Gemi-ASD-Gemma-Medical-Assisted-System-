# llm/gemma_wrapper.py
import contextlib
import os, sys
import json
import concurrent.futures
import asyncio
from pathlib import Path
from functools import partial

from llama_cpp import Llama
from text_utils import clean_emoji_text
from .prompt_builder import build_emergency_prompt  # 👈 solo este

# ──────────────────────────────────────────────────────────────
# Modelo Gemma cargado sin imprimir logs en consola
# ──────────────────────────────────────────────────────────────
def _get_model_path() -> Path:
    """
    Devuelve la ruta al .gguf:
     - Si estamos en un EXE --onefile, mira en sys._MEIPASS/models/…
     - En desarrollo, mira en <project_root>/models/…
    """
    rel = Path("models") / "gemma3n" / "gemma-3n-2b-it-gguf" / "gemma-3n-E2B-it-Q4_K_M.gguf"

    if getattr(sys, "_MEIPASS", None):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent

    model_path = base / rel
    if not model_path.exists():
        raise FileNotFoundError(
            f"Gemma model not found at {model_path!r}\n"
            "  • En local, asegúrate de tener ./models/gemma3n/gemma-3n-2b-it-gguf/…\n"
            "  • En EXE, compílalo con --add-data \"models;models\""
        )
    return model_path

# ──────────────────────────────────────────────────────────────
# Cargamos el modelo sin imprimir logs en consola
# ──────────────────────────────────────────────────────────────
_fnull = open(os.devnull, 'w')
with contextlib.redirect_stdout(_fnull), contextlib.redirect_stderr(_fnull):
    MODEL_PATH = _get_model_path()
    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=1024,
        n_threads=max(os.cpu_count() // 2, 2),
        chat_format="gemma",
        low_vram=True,
        verbose=False,
    )
# ──────────────────────────────────────────────────────────────

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

def _call(messages, **kw):
    out = llm.create_chat_completion(messages=messages, **kw)
    return out["choices"][0]["message"]["content"].strip()

async def medichat_async(user_text: str):
    # import local para evitar ciclos
    from .prompt_builder import build_chat_prompt

    messages, chat_file = build_chat_prompt(user_text)

    fn   = partial(_call, messages, temperature=0.8, top_p=0.9, max_tokens=1000)
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(_executor, fn)

    cleaned_reply = clean_emoji_text(reply)
    messages.append({"role": "assistant", "content": cleaned_reply})

    chat_file.write_text(
        json.dumps(messages, indent=2, ensure_ascii=False),
        encoding="utf-8",
        errors="ignore",
    )
    return cleaned_reply

async def emergency_async(extra_user_message: str = ""):
    sys_msgs = build_emergency_prompt()
    if extra_user_message:
        sys_msgs.append({"role": "user", "content": extra_user_message})

    fn = partial(
        _call,
        sys_msgs,
        temperature=0.25,
        top_p=0.5,
        max_tokens=600,              # ⬆ más tokens
    )
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(_executor, fn)
    return clean_emoji_text(reply)
