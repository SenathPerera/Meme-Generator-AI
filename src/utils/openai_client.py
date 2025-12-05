"""
openai_client.py
----------------
Centralized helper for OpenAI API calls (text, embeddings, moderation, image).
Automatically switches between paid mode and fallback mode.
"""

import os, base64
from src.utils.config import (
    OPENAI_API_KEY, OPENAI_TEXT_MODEL, OPENAI_IMAGE_MODEL,
    OPENAI_TIMEOUT, USE_PAID_API, OPENAI_ORG_ID, OPENAI_PROJECT_ID
)
from openai import OpenAI

# -----------------------------------------------------
# ✅ Initialize global OpenAI client safely
# -----------------------------------------------------
client = None
if USE_PAID_API and OPENAI_API_KEY:
    try:
        # Pass org / project explicitly if provided
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_ORG_ID:
            kwargs["organization"] = OPENAI_ORG_ID
        if OPENAI_PROJECT_ID:
            kwargs["project"] = OPENAI_PROJECT_ID

        client = OpenAI(**kwargs)
        print(f"✅ OpenAI client ready (model={OPENAI_TEXT_MODEL}, "
              f"org={OPENAI_ORG_ID or 'default'}, proj={OPENAI_PROJECT_ID or 'default'})")
    except Exception as e:
        print(f"⚠️ Failed to initialize OpenAI client: {e}")
else:
    print("⚠️ OpenAI client disabled (USE_PAID_API=false or missing key)")


# -----------------------------------------------------
# 🧠 Unified helper functions
# -----------------------------------------------------
def openai_chat(messages, model: str = None, max_tokens: int = 200, temperature: float = 0.7):
    """
    Generate chat completion text using OpenAI API.
    """
    if not client:
        raise RuntimeError("OpenAI client unavailable")

    model = model or OPENAI_TEXT_MODEL
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=OPENAI_TIMEOUT,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI chat error: {e}")
        raise RuntimeError("OpenAI client unavailable")


def openai_embed(texts):
    """
    Create embeddings using OpenAI embedding API.
    """
    if not client:
        raise RuntimeError("OpenAI client unavailable")

    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
            timeout=OPENAI_TIMEOUT,
        )
        return [d.embedding for d in response.data]
    except Exception as e:
        print(f"⚠️ OpenAI embedding error: {e}")
        raise RuntimeError("OpenAI client unavailable")


def openai_moderate(text: str):
    """
    Returns (ok: bool, reason: str).
    Uses omni-moderation-latest via the new OpenAI SDK (>=1.x).
    """
    if not client:
        return True, "skip_openai"

    try:
        resp = client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
        # resp.results is a list of objects; use attributes, not dict indexing
        flagged = any(getattr(r, "flagged", False) for r in resp.results)
        return (not flagged, "ok" if not flagged else "flagged")
    except Exception as e:
        print("⚠️ OpenAI moderation error:", e)
        return True, "openai_error"



def openai_image(prompt, out_path="outputs/openai_image.png"):
    if not client:
        raise RuntimeError("OpenAI client unavailable")
    resp = client.images.generate(
        model=OPENAI_IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024",
    )
    b64 = resp.data[0].b64_json
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    print("🖼️ OpenAI image generated ->", out_path)   # <- make sure this is present
    return out_path

# --- Context → (image_prompt, captions[]) planner ---
def openai_plan_from_context(context: str) -> dict:
    """
    Returns {"image_prompt": str, "captions": [str, ...]} using the chat model.
    The image_prompt is safe (no text rendering, no logos/brands/people),
    captions are short and meme-y.
    """
    if not client:
        raise RuntimeError("OpenAI client unavailable")

    system = (
        "You are a meme planner. Given a user context, produce:\n"
        "1) image_prompt: a safe, original visual description (NO text in the image, "
        "   NO brand names, NO logos, NO celebrities, NO explicit content). "
        "   The background should have clean space at top and bottom for text overlay.\n"
        "2) captions: 3-5 short, funny meme captions. Use clean humor; avoid slurs/NSFW.\n"
        "Return STRICT JSON with keys: image_prompt, captions."
    )

    user = (
        f"Context: {context}\n"
        "Output JSON only. Example:\n"
        "{\n"
        '  "image_prompt": "abstract office scene... (no text, safe, generic)",\n'
        '  "captions": ["TOP // BOTTOM", "single line", "POV: ..."]\n'
        "}"
    )

    try:
        resp = client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.8,
            max_tokens=400,
        )
        raw = resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"openai_plan_from_context error: {e}")

    # Loose JSON recovery
    import json, re
    try:
        j = json.loads(raw)
    except Exception:
        # try to find a JSON block
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            raise RuntimeError("Planner returned non-JSON")
        j = json.loads(m.group(0))

    # normalize
    prompt = (j.get("image_prompt") or "").strip()
    caps = [c.strip() for c in (j.get("captions") or []) if c and isinstance(c, str)]
    if not prompt:
        raise RuntimeError("Planner missing image_prompt")
    if not caps:
        caps = ["WHEN THE CONTEXT HITS", "POV: MONDAY ENERGY", "RELATABLE // CHAOS MODE"]
    return {"image_prompt": prompt, "captions": caps[:5]}

def openai_plan_search(context: str) -> dict:
    """
    Return {"search_prompt": str, "tags": [str,...]} from user context.
    Safe, generic terms (no brands/people/NSFW). Uses chat model.
    """
    if not client:
        # safe fallback
        return {"search_prompt": context.strip(), "tags": []}

    system = (
        "You turn user context into generic meme template search queries. "
        "Output clean, safe keywords (no brands/celebrities)."
    )
    user = (
        f"Context: {context}\n"
        "Return JSON only:\n"
        "{\n"
        '  \"search_prompt\": \"short phrase to search templates\",\n'
        '  \"tags\": [\"upset\", \"office\", \"tired\", \"two-panel\"]\n'
        "}"
    )
    resp = client.chat.completions.create(
        model=OPENAI_TEXT_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.6,
        max_tokens=200,
    )
    raw = resp.choices[0].message.content.strip()

    import json, re
    try:
        j = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S); j = json.loads(m.group(0)) if m else {}
    return {
        "search_prompt": (j.get("search_prompt") or context).strip()[:120],
        "tags": [t.strip() for t in (j.get("tags") or []) if isinstance(t, str)][:8],
    }


