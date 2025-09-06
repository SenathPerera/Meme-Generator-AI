import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
COMPLIANCE_LOG = LOG_DIR / "compliance_logs.csv"

GENERATED_DIR = PROJECT_ROOT / "generated_memes"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("HOST", "localhost")
PORT_IDEA = int(os.getenv("PORT_IDEA", 5001))
PORT_TEMPLATES = int(os.getenv("PORT_TEMPLATES", 5002))
PORT_GENERATOR = int(os.getenv("PORT_GENERATOR", 5003))
PORT_SECURITY = int(os.getenv("PORT_SECURITY", 5004))

SECURITY_KEY = os.getenv("SECURITY_KEY", "my_secret_key")
IMGFLIP_USER = os.getenv("IMGFLIP_USER", "imgflip_hubot")
IMGFLIP_PASS = os.getenv("IMGFLIP_PASS", "imgflip_hubot")

# Optional image hosting fallback (no secret): https://apidocs.imgur.com/
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "").strip()

URL_IDEA = f"http://{HOST}:{PORT_IDEA}/get_idea"
URL_TEMPLATES = f"http://{HOST}:{PORT_TEMPLATES}/get_templates"
URL_TEMPLATES_SEARCH = f"http://{HOST}:{PORT_TEMPLATES}/search_templates"
URL_GENERATE = f"http://{HOST}:{PORT_GENERATOR}/generate_meme"
