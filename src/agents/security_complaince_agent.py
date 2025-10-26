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

# ---------- 1️ OpenAI Moderation ----------
    def _check_openai_moderation(self, caption: str):
        """Check caption using the OpenAI moderation API via openai_client."""
        try:
            ok, detail = openai_moderate(caption)
            if not ok:
                return False, f"openai_flagged ({detail})"
            return True, "openai_ok"
        except Exception as e:
            print("⚠️ OpenAI moderation error:", e)
            return True, "openai_error"

    # ---------- 2️ Local banned-words ----------
    def _check_banned(self, caption: str):
        """Check caption for banned keywords locally."""
        tokens = re.findall(r"[a-zA-Z']+", caption.lower())
        hits = sorted({t for t in tokens if t in BANNED})
        if hits:
            return False, f"banned terms {hits}"
        return True, "ok"

    # ---------- 3️ Hugging Face Toxic-BERT ----------
    def _check_hf_detoxify(self, caption: str, threshold: float = 0.80):
        """Check caption toxicity using Hugging Face model (unitary/toxic-bert)."""
        try:
            url = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
            headers = {"Content-Type": "application/json"}
            if HUGGINGFACE_API_TOKEN:
                headers["Authorization"] = f"Bearer {HUGGINGFACE_API_TOKEN}"  # optional auth
            r = requests.post(url, headers=headers, json={"inputs": caption}, timeout=15)
            if not r.ok:
                return True, "hf_skip"

            data = r.json()
            scores = [cls.get("score", 0.0) for item in data for cls in item]
            if scores and max(scores) > threshold:
                return False, f"toxic score {max(scores):.2f}"
            return True, "hf_ok"
        except Exception as e:
            print("⚠️ HF detoxify error:", e)
            return True, "hf_error"
        
 # ---------- 4️ Google Perspective API ----------
    def _check_perspective(self, caption: str, threshold: float = 0.80):
        """Use Google Perspective API to check toxicity, insult, profanity."""
        try:
            if not PERSPECTIVE_API_KEY:
                return True, "perspective_skip"

            url = (
                f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
                f"?key={PERSPECTIVE_API_KEY}"
            )
            r = requests.post(
                url,
                json={
                    "comment": {"text": caption},
                    "requestedAttributes": {
                        "TOXICITY": {},
                        "INSULT": {},
                        "PROFANITY": {},
                    },
                    "languages": ["en"],
                },
                timeout=15,
            )
            if not r.ok:
                return True, "perspective_err"

            j = r.json()
            scores = [
                j["attributeScores"].get(attr, {}).get("summaryScore", {}).get("value", 0.0)
                for attr in ["TOXICITY", "INSULT", "PROFANITY"]
            ]
            if scores and max(scores) > threshold:
                return False, f"perspective high {max(scores):.2f}"
            return True, "perspective_ok"
        except Exception as e:
            print("⚠️ Perspective API error:", e)
            return True, "perspective_error"

    # ---------- MAIN COMPLIANCE CHECK ----------
    def check(self, caption: str) -> ComplianceResult:
        """Run all security checks and return overall result."""

        # 1️ OpenAI moderation
        ok, detail = self._check_openai_moderation(caption)
        if not ok:
            self._log(caption, "BLOCKED", detail)
            return ComplianceResult(False, f"Blocked: {detail}")

        # 2️ Local banned words
        ok, detail = self._check_banned(caption)
        if not ok:
            self._log(caption, "BLOCKED", detail)
            return ComplianceResult(False, f"Blocked: {detail}")

        # 3️ Hugging Face toxicity
        ok, detail = self._check_hf_detoxify(caption)
        if not ok:
            self._log(caption, "BLOCKED", detail)
            return ComplianceResult(False, f"Blocked: {detail}")

        # 4️ Perspective API
        ok, detail = self._check_perspective(caption)
        if not ok:
            self._log(caption, "BLOCKED", detail)
            return ComplianceResult(False, f"Blocked: {detail}")

        # Passed all checks
        self._log(caption, "PASSED", "ok")
        return ComplianceResult(True, "OK")



