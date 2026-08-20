import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el .env si existe
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
WORKSTREAM_API_KEY = os.getenv("WORKSTREAM_API_KEY", "")
WORKSTREAM_BASE_URL = os.getenv("WORKSTREAM_BASE_URL", "https://api.workstream.is/v1")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

STORE_ADDRESS = os.getenv("STORE_ADDRESS", "Stafford, TX 77477")
STORE_NAME = os.getenv("STORE_NAME", "Chick-fil-A Stafford")

# Modelo por defecto
DEFAULT_MODEL = "gpt-4o-mini"
REASONING_MODEL = "gpt-4o"
