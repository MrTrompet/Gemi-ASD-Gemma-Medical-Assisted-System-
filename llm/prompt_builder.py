# llm/prompt_builder.py
import json
import os
import datetime
from pathlib import Path
from text_utils import clean_emoji_text

# 1) Definir APPDATA\GemiASD
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home()/"AppData"/"Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# 2) Usar esa carpeta directamente
PROFILE   = APPDATA_DIR / "gemi_user_data.json"
CHAT_FILE = APPDATA_DIR / "chat_data.json"

# Prompt genérico para chat
SYSTEM_PROMPT = (
    "You are Gemi, a friendly medical assistant."
    "Respond in a clear, professional, and concise manner."
)


def _load(path: Path, default):
    if not path.exists():
        return default
    txt = path.read_text(encoding="utf-8").strip()
    return json.loads(txt) if txt else default


def build_emergency_prompt() -> list[dict]:
    """
    Genera el prompt de emergencia (objetos JSON con nivel y mensaje).
    Conservamos esta función para el flujo de primeros auxilios.
    """
    data = _load(PROFILE, {})
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    profile      = data.get("profile", {})
    gender       = profile.get("gender", "?")
    age          = profile.get("age", "?")
    background = ", ".join(data.get("background", [])) or "None"
    symptoms     = ", ".join(data.get("symptoms", []))     or "No symptoms"

    system_msg = (
        "You are Gemi ADS, an OFF-LINE first aid assistant.\n"
        "ALWAYS return a JSON object with no extra text.\n"
        "Format:\n"
        '{ "level": "green|yellow|red", "message": "<brief recommendations>" }'
    )

    user_msg = (
        "Evaluate the risk of stroke with this information.\n"
        f"Profile: {gender}, {age} years old\n"
        f"Background: {background}\n"
        f"Current symptoms ({ts}): {symptoms}"
    )

    return [
        {"role": "system",  "content": clean_emoji_text(system_msg)},
        {"role": "user",    "content": clean_emoji_text(user_msg)},
    ]


def build_chat_prompt(user_msg: str) -> tuple[list[dict], Path]:
    """
    Always build a chat prompt with:
      1) System message (SYSTEM_PROMPT)
      2) Up to 9 previous messages (from chat_data.json)
      3) The current user message

    Returns the list of messages and the save path.
    """
    history = _load(CHAT_FILE, [])
    # Mantener solo últimas 9 para no exceder tokens
    history = history[-9:]
    # Insertar el prompt de sistema si no está
    if not history or history[0]["role"] != "system":
        history.insert(0, {"role": "system", "content": clean_emoji_text(SYSTEM_PROMPT)})
    # Añadir el mensaje nuevo del usuario
    history.append({"role": "user", "content": clean_emoji_text(user_msg)})
    return history, CHAT_FILE
