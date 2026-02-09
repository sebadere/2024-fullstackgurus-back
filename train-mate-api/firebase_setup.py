import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from pathlib import Path
from typing import Optional

# Try to load environment variables from a .env file (for local development)
from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent
_DOTENV_PATH = _BASE_DIR / ".env"

# Load .env only if it exists (safe for Render which does not use .env)
if _DOTENV_PATH.exists():
    load_dotenv(dotenv_path=_DOTENV_PATH)
else:
    load_dotenv()


def _load_firebase_credentials_json() -> Optional[str]:
    firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
    firebase_creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    candidate = firebase_creds or firebase_creds_path
    if candidate:
        candidate = candidate.strip()
        if candidate.lstrip().startswith("{"):
            return candidate

        path = Path(candidate)
        if not path.is_absolute():
            path = (_BASE_DIR / path).resolve()
        if path.exists():
            return path.read_text(encoding="utf-8")

        raise Exception(f"FIREBASE_CREDENTIALS path not found: {path}")

    # Fallback: look for a service account file in the project root
    for path in sorted(_BASE_DIR.glob("*firebase-adminsdk*.json")):
        return path.read_text(encoding="utf-8")

    default_path = _BASE_DIR / "serviceAccountKey.json"
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")

    return None


firebase_creds_json = _load_firebase_credentials_json()
if firebase_creds_json:
    # Parse the JSON string (from the environment variable or file)
    firebase_creds_dict = json.loads(firebase_creds_json)

    # Initialize Firebase with the credentials loaded from environment variables
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_creds_dict)
        firebase_admin.initialize_app(cred)

    # Initialize Firestore
    db = firestore.client()
else:
    raise Exception(
        "Firebase credentials not found. Set FIREBASE_CREDENTIALS (JSON) or "
        "FIREBASE_CREDENTIALS_PATH, or place a *firebase-adminsdk*.json file in "
        "train-mate-api."
    )
