import os
import json
from typing import Dict, List
import requests


GROK_API_URL = os.getenv("GROK_API_URL", "https://api.x.ai/v1/chat/completions").strip()
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-latest").strip()


def _mask(key: str) -> str:
    if not key:
        return ""
    return f"{key[:6]}…{key[-4:]}" if len(key) > 12 else key[:3] + "…"


def _debug_grok_config():
    key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY") or ""
    try:
        print("🧩 GROK CONFIG:")
        print("  GROK_MODEL =", GROK_MODEL)
        print("  GROK_API_URL =", GROK_API_URL)
        if key:
            print("  GROK_API_KEY starts with:", _mask(key))
            print("✅ Grok client ready (model=", GROK_MODEL, ")", sep="")
        else:
            print("  GROK_API_KEY not set (will fallback if used)")
    except Exception:
        # Avoid breaking import on printing issues
        pass


# Emit a one-time debug line on import so startup mirrors OpenAI debug
_debug_grok_config()


def _get_api_key() -> str:
    key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing GROK_API_KEY (or XAI_API_KEY). Add it to your .env at the project root."
        )
    return key


def generate_with_grok(context: str) -> Dict:
    """
    Call xAI Grok chat API to produce a planning response with the shape:
    {"image_prompt": str, "captions": [str, ...]}.
    """
    api_key = _get_api_key()

    system = (
        "You are a meme planning assistant. Return a compact JSON object with two keys: "
        "image_prompt (a concise scene description) and captions (an array of 3-6 short meme captions). "
        "Do not include any extra commentary."
    )
    user = (
        f"Context: {context}\n\n"
        "Respond ONLY with JSON in this exact schema: "
        "{\"image_prompt\":\"...\",\"captions\":[\"...\",\"...\"]}"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.8,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }

    try:
        print(f"[grok] POST {GROK_API_URL} model={GROK_MODEL} ctx_len={len(context)}")
        resp = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=60)
        status = resp.status_code
        print(f"[grok] response status={status}")
    except Exception as e:
        print("[grok] request error:", e)
        raise
    resp.raise_for_status()
    data = resp.json()

    # xAI response is OpenAI-compatible
    content = (
        data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "{}")
    )
    rid = data.get("id") or data.get("request_id")
    if rid:
        print(f"[grok] response id={rid} content_len={len(content)}")
    try:
        obj = json.loads(content)
    except Exception:
        # Last-ditch attempt: sometimes models wrap code blocks
        content = content.strip().strip("` ")
        obj = json.loads(content)

    image_prompt = str(obj.get("image_prompt", "Make a meme-ready background.")).strip()
    captions_raw = obj.get("captions", [])
    captions: List[str] = [str(c).strip() for c in captions_raw if str(c).strip()]
    if not captions:
        captions = [
            "POV: it escalated quickly",
            "When the plot twist hits",
            "Me pretending it’s fine",
        ]

    return {"image_prompt": image_prompt, "captions": captions[:6]}
