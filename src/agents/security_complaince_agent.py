import os, requests, re, csv, datetime
from dataclasses import dataclass
from src.utils.config import (
    COMPLIANCE_LOG,
    BANNED_WORDS_FILE,
    PERSPECTIVE_API_KEY,
    HUGGINGFACE_API_TOKEN,
)
from src.utils.openai_client import openai_moderate


# ---------------------------------------------------------
# Compliance Result Data Model
# ---------------------------------------------------------
@dataclass
class ComplianceResult:
    ok: bool
    reason: str


# ---------------------------------------------------------
# Load local banned-words list
# ---------------------------------------------------------
def _load_banned_words():
    """Load banned words from file or fallback to default list."""
    try:
        with open(BANNED_WORDS_FILE, "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f if w.strip()]
    except Exception:
        # Default fallback list
        return ["kill", "suicide", "hate", "racist", "nazi", "terrorist", "bomb", "rape"]


BANNED = set(_load_banned_words())


# ---------------------------------------------------------
# Security & Compliance Agent
# ---------------------------------------------------------
class SecurityComplianceAgent:
    """
    Multi-check compliance pipeline:
    OpenAI Moderation API (omni-moderation-latest)
    Local banned-word list
    Hugging Face Toxic-BERT (unitary/toxic-bert)
    Google Perspective API (optional)
    Logs all checks to /logs/compliance_logs.csv
    """

    def __init__(self, log_path=COMPLIANCE_LOG):
        self.log_path = log_path

    # ---------- Logging ----------
    def _log(self, caption, status, detail):
        """Write compliance result to CSV log."""
        COMPLIANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [datetime.datetime.utcnow().isoformat(), status, caption, detail]
            )