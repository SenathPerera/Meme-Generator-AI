from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio, hashlib, time
from typing import Optional, Dict
import re


app = FastAPI(title="Security & Compliance Agent", version="1.0")


RATE_LIMIT = 40            
RATE_WINDOW = 60          
_bucket: Dict[str, Dict[str, float]] = {}
_lock = asyncio.Lock()

def _client_sig(api_key: str, addr: str) -> str:
    raw = (api_key or "") + "|" + (addr or "0.0.0.0")
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

async def _rate_limit(sig: str) -> bool:
    now = time.time()
    async with _lock:
        rec = _bucket.get(sig, {"count": 0, "reset": now + RATE_WINDOW})
        if now > rec["reset"]:
            rec = {"count": 0, "reset": now + RATE_WINDOW}
        rec["count"] += 1
        _bucket[sig] = rec
        return rec["count"] <= RATE_LIMIT
    

# ---------- Models ----------
class SecureReq(BaseModel):
    action: str                     # idea | templates | search_templates | generate
    payload: Dict[str, str] = {}


# security policy part
HATE = {"racist", "hate", "white power", "ethnic cleansing", "nazi", "nazism"}
HARASS = {"kill yourself", "idiot", "stupid", "loser", "dumb", "die", "trash human"}
VIOLENCE = {"shoot", "stab", "bomb", "terror", "attack", "behead"}
SEXUAL = {"porn", "rape", "nude", "explicit"}
SELF_HARM = {"self harm", "suicide", "kill myself", "cut myself"}

BAD_PATTERNS = [
    r"<\s*script\b", r"onerror\s*=", r"DROP\s+TABLE", r";--", r"UNION\s+SELECT",
    r"insert\s+into", r"delete\s+from"
]
PII_PATTERNS = [
    r"\b\d{10}\b",
    r"\b\d{12}\b",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
]

POLICY = {
    "hate_speech": HATE,
    "harassment": HARASS,
    "violence": VIOLENCE,
    "sexual_content": SEXUAL,
    "self_harm": SELF_HARM
}