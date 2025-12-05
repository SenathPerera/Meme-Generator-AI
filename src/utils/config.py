import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths
THIS = Path(__file__).resolve()
SRC_DIR = THIS.parents[1]
PROJ_DIR = SRC_DIR.parents[1]

# -----------------------------------
# Force-load .env from project root
# -----------------------------------
from dotenv import load_dotenv
from pathlib import Path
import os

# Explicitly resolve path two levels up (project root)
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

if ENV_PATH.exists():
    print(f"🔍 Loading environment from: {ENV_PATH}")
    load_dotenv(ENV_PATH, override=True)
else:
    print(f"⚠️ .env not found at: {ENV_PATH}")


print("🧩 DEBUG CONFIG:")
print("  USE_PAID_API =", os.getenv("USE_PAID_API"))
print("  OPENAI_API_KEY starts with:", str(os.getenv("OPENAI_API_KEY"))[:10])

# Branding
APP_NAME      = os.getenv("APP_NAME", "MemeForge AI")
APP_TAGLINE   = os.getenv("APP_TAGLINE", "Text ➜ Template ➜ Edit ➜ Safe Download")
BRAND_PRIMARY = os.getenv("BRAND_PRIMARY", "#4F46E5")
BRAND_ACCENT  = os.getenv("BRAND_ACCENT", "#06B6D4")
LOGO_PATH     = os.getenv("LOGO_PATH", "data/brand/logo.png")

# Data / assets
DATA_DIR      = SRC_DIR / "data"
FONTS_DIR     = DATA_DIR / "fonts"
FONT_PATH     = os.getenv("FONT_PATH", str(FONTS_DIR / "Impact.ttf"))

# Logs
LOGS_DIR      = PROJ_DIR / "logs"
COMPLIANCE_LOG= LOGS_DIR / "compliance_logs.csv"

# Models (free)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CAPTION_MODEL   = os.getenv("CAPTION_MODEL", "distilgpt2")

# IR
TOP_K_TEMPLATES = int(os.getenv("TOP_K_TEMPLATES", "10"))

# Policy
BANNED_WORDS_FILE = os.getenv("BANNED_WORDS_FILE", str(DATA_DIR / "policy" / "banned_words.txt"))

# Optional API keys
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
DEEPAI_API_KEY        = os.getenv("DEEPAI_API_KEY", "").strip()
PERSPECTIVE_API_KEY   = os.getenv("PERSPECTIVE_API_KEY", "").strip()
OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY", "").strip()

# ==== NEW OPENAI CONFIG (for paid API) ====
USE_PAID_API       = os.getenv("USE_PAID_API", "true").lower() == "true"
OPENAI_TEXT_MODEL  = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
OPENAI_TIMEOUT     = int(os.getenv("OPENAI_TIMEOUT", "60"))
OPENAI_ORG_ID     = os.getenv("OPENAI_ORG_ID", "").strip()
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID", "").strip()

# Ensure directories exist
for p in [FONTS_DIR, LOGS_DIR, DATA_DIR / "policy"]:
    Path(p).mkdir(parents=True, exist_ok=True)
