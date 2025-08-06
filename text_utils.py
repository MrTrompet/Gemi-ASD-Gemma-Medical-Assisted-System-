#text_utils.py

# text_utils.py  (colócalo en la raíz del proyecto)

def clean_emoji_text(text: str) -> str:
    """
    Elimina emojis y cualquier carácter fuera del ASCII para
    evitar UnicodeEncodeError en Windows/CP-1252.
    """
    # encode→decode con ASCII + errors='ignore' borra lo no-ASCII
    return text.encode("latin-1", errors="ignore").decode("latin-1")
