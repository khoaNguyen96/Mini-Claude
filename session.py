import json
import os

# PLACEHOLDER: SESSION_FILE is used by the chapter's code but never defined in it
SESSION_FILE = ".mini-claude-session.json"


def save_session(messages) -> None:
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, default=lambda o: getattr(o, "model_dump", lambda: str(o))())
    except Exception:
        pass

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

