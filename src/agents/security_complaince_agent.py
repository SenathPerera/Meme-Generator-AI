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
