# utils.py

import json
import re
import os
import shutil
import asyncio
from pathlib import Path
from datetime import datetime    # <-- Import necesario para la serialización
from typing import Dict, Any, List

from text_utils import clean_emoji_text        # única función de limpieza
from llm.gemma_wrapper import (
    medichat_async,
    emergency_async,
)

# 1) Definir APPDATA\GemiASD como carpeta de datos
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home()/"AppData"/"Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Rutas de datos
# ------------------------------------------------------------------
DATA_DIR        = APPDATA_DIR
PROFILE_PATH    = DATA_DIR / "profile_data.json"
CHAT_DATA_PATH  = DATA_DIR / "chat_data.json"
USER_DATA_PATH  = DATA_DIR / "gemi_user_data.json"
PDF_CACHE_DIR   = DATA_DIR / "pdfs"
PHOTOS_DIR      = DATA_DIR / "photos"
ASSETS_DIR      = DATA_DIR / "assets"

# ------------------------------------------------------------------
# Limpieza de datos y cachés
# ------------------------------------------------------------------
def clear_user_data() -> None:
    """
    Borra todos los JSONs de usuario/chat y limpia cachés de PDFs y fotos.
    """
    # Eliminar archivos JSON
    for p in (USER_DATA_PATH, PROFILE_PATH, CHAT_DATA_PATH):
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    # Limpiar caché de PDFs
    if PDF_CACHE_DIR.exists():
        shutil.rmtree(PDF_CACHE_DIR)
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Limpiar fotos de perfil
    if PHOTOS_DIR.exists():
        shutil.rmtree(PHOTOS_DIR)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Utilidades de fichero
# ------------------------------------------------------------------
def ensure_data_dir() -> Path:
    """
    Asegura que la carpeta DATA_DIR exista y la devuelve.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR

def load_json(path: Path) -> Dict[str, Any]:
    """
    Carga un JSON desde la ruta indicada. Si no existe, devuelve {}.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        return {}
    try:
        txt = path.read_text(encoding="utf-8").strip()
        return json.loads(txt) if txt else {}
    except json.JSONDecodeError:
        return {}

def save_json(data: Any, path: Path) -> None:
    """
    Guarda cualquier objeto en JSON, convirtiendo los datetime a strings ISO.
    Crea la carpeta si hace falta.
    """
    # Asegurar directorio
    path.parent.mkdir(parents=True, exist_ok=True)

    def _default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        # Añade aquí otros tipos si es necesario
        raise TypeError(f"Type {o.__class__.__name__} not serializable")

    text = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        default=_default
    )
    path.write_text(text, encoding="utf-8")


# ------------------------------------------------------------------
# Perfil y datos de usuario
# ------------------------------------------------------------------
def load_user_data(path: Path) -> Dict[str, Any]:
    return load_json(path)

def save_user_data(data: Dict[str, Any], path: Path) -> None:
    save_json(data, path)

def load_profile_data() -> Dict[str, Any]:
    return load_json(PROFILE_PATH)

def save_profile_data(data: Dict[str, Any]) -> None:
    save_json(data, PROFILE_PATH)

def save_profile_photo(src_path: str) -> str:
    photos_dir = PHOTOS_DIR
    photos_dir.mkdir(parents=True, exist_ok=True)
    dest = photos_dir / Path(src_path).name
    try:
        shutil.copy(src_path, dest)
    except Exception:
        pass
    return str(dest)


# ------------------------------------------------------------------
# Chat data persistence
# ------------------------------------------------------------------
def save_chat_data(data: List[Dict[str, str]], path: Path) -> None:
    """
    Guarda el historial de chat (solo roles user y assistant) en JSON,
    limpiando emojis y markdown.
    """
    cleaned = []
    for msg in data:
        if msg.get("role") in ("user", "assistant"):
            cleaned.append({
                "role": msg["role"],
                "content": clean_emoji_text(msg["content"])
            })
    save_json(cleaned, path)


# ------------------------------------------------------------------
# Emergency stubs (sincrónicos)
# ------------------------------------------------------------------

async def run_gemma_emergency(payload: Dict[str, Any]) -> Dict[str, str]:
    await asyncio.sleep(1)
    count = len(payload.get("symptoms", []))
    high = {"Atrial fibrillation", "previous Stroke/TIA", "Cardiovascular disease"}
    score = count + (1 if any(a in high for a in payload.get("antecedentes", [])) else 0)
    if score >= 4:
        return {"level": "red", "message": "High risk, call emergency services."}
    if score >= 2:
        return {"level": "yellow", "message": "Medium risk, seek urgent attention."}
    return {"level": "green", "message": "Low risk, remain attentive."}


# ------------------------------------------------------------------
# Stub chat síncrono (tests/offline)
# ------------------------------------------------------------------
async def run_gemma_medichat(messages: List[Dict[str, str]]) -> str:
    await asyncio.sleep(1)
    if not messages:
        return "Hello, I'm Gemi. How can I help you today?"
    txt = messages[-1]["content"].lower()
    if any(w in txt for w in ["fever", "temp"]):
        return "If you have a fever, stay hydrated and monitor your temperature."
    return "I am analyzing your query..."


# ------------------------------------------------------------------
# Wrappers: llaman al modelo real (llm.gemma_wrapper)
# ------------------------------------------------------------------
async def run_gemma_medichat_async(history: List[Dict[str, str]]) -> str:
    """
    Envía al modelo real la conversación completa como un prompt concatenado.
    """
    cleaned = [
        {"role": m["role"], "content": clean_emoji_text(m["content"])}
        for m in history
    ]
    lines: List[str] = []
    for m in cleaned:
        if m["role"] == "system":
            lines.append(m["content"])
        elif m["role"] == "user":
            lines.append(f"Usuario: {m['content']}")
        else:
            lines.append(f"Gemi: {m['content']}")
    prompt = "\n".join(lines)
    reply = await medichat_async(prompt)
    return clean_emoji_text(reply)

async def run_gemma_emergency_async(payload: Dict[str, Any]) -> Dict[str, str]:
    level = _score_payload(payload)
    extra_msg = (
        f"Calculated Level: {level.upper()}. "
        "Briefly explain why and offer 2-4 immediate steps for the patient."
    )
    txt = await emergency_async(extra_user_message=extra_msg)
    clean = clean_emoji_text(txt)
    try:
        data = json.loads(clean)
        if isinstance(data, dict) and "level" in data and "message" in data:
            return data
    except json.JSONDecodeError:
        pass
    return {"level": level, "message": clean}


# ------------------------------------------------------------------
# Helper para scoring de emergencias
# ------------------------------------------------------------------
def _score_payload(payload: Dict[str, Any]) -> str:
    score = len(payload.get("symptoms", []))
    high = {
         "Hypertension", "High cholesterol", "Smoking",
         "Diabetes", "Atrial fibrillation", "Previous stroke/TIA",
         "Cardiovascular disease",
    }
    score += sum(1 for a in payload.get("background", []) if a in high)
    if payload.get("profile", {}).get("age", 0) >= 60:
        score += 1
    return "red" if score >= 4 else "yellow" if score >= 2 else "green"

