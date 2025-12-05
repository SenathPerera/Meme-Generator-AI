import requests
from typing import List, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
from src.utils.config import (
    CAPTION_MODEL,
    HUGGINGFACE_API_TOKEN,
    DEEPAI_API_KEY,
)
from src.utils.openai_client import openai_chat
from src.utils.openai_client import openai_plan_from_context

# ---------------------------------------
# Local + API-based caption generation
# ---------------------------------------
# Local fallback GPT-2
_tokenizer = AutoTokenizer.from_pretrained(CAPTION_MODEL)
_model = AutoModelForCausalLM.from_pretrained(CAPTION_MODEL)


# ---------- 1️⃣ OpenAI (paid primary) ----------
def _openai_generate(prompt: str, n: int = 3) -> List[str]:
    """Generate witty meme captions using OpenAI GPT models."""
    ideas = []
    try:
        for _ in range(n):
            txt = openai_chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a witty meme caption generator. "
                                   "Write short, funny, relatable captions suitable for memes."
                    },
                    {"role": "user", "content": f"Write a meme caption for: {prompt}"}
                ],
                max_tokens=50,
                temperature=0.9,
            )
            if txt:
                ideas.append(txt.strip().replace('"', "").replace("`", ""))
    except Exception as e:
        print("⚠️ OpenAI caption generation failed:", e)
    return ideas


# ---------- 2️⃣ Local GPT-2 (offline fallback) ----------
def _local_generate(prompt: str, n: int = 3) -> List[str]:
    """Fallback: generate meme captions locally using GPT-2."""
    try:
        inputs = _tokenizer.encode(prompt, return_tensors="pt")
        outputs = _model.generate(
            inputs,
            max_length=40,
            num_return_sequences=n,
            do_sample=True,
            temperature=0.9,
            top_p=0.95,
        )
        out = []
        for seq in outputs:
            txt = _tokenizer.decode(seq, skip_special_tokens=True)
            txt = txt.replace(prompt, "").strip().split("\n")[0][:60]
            if txt:
                out.append(txt)
        return out
    except Exception as e:
        print("⚠️ Local GPT-2 caption generation error:", e)
        return []


# ---------- 3️⃣ Hugging Face Inference API ----------
def _hf_inference(prompt: str, n: int = 3) -> List[str]:
    """Free API fallback using HuggingFace inference endpoint."""
    try:
        url = "https://api-inference.huggingface.co/models/gpt2"
        headers = {"Content-Type": "application/json"}
        if HUGGINGFACE_API_TOKEN:
            headers["Authorization"] = f"Bearer {HUGGINGFACE_API_TOKEN}"

        r = requests.post(
            url,
            headers=headers,
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 40,
                    "num_return_sequences": n
                }
            },
            timeout=15
        )
        if not r.ok:
            return []
        data = r.json()
        results = []
        for item in data:
            txt = item.get("generated_text", "").replace(prompt, "").strip()
            if txt:
                results.append(txt.split("\n")[0][:60])
        return results
    except Exception as e:
        print("⚠️ HuggingFace inference error:", e)
        return []


# ---------- 4️⃣ DeepAI free API ----------
def _deepai(prompt: str) -> List[str]:
    """Free API fallback using DeepAI text generator."""
    try:
        if not DEEPAI_API_KEY:
            return []
        r = requests.post(
            "https://api.deepai.org/api/text-generator",
            data={"text": prompt},
            headers={"api-key": DEEPAI_API_KEY},
            timeout=15
        )
        if not r.ok:
            return []
        txt = r.json().get("output", "").split("\n")[0][:60].strip()
        return [txt] if txt else []
    except Exception as e:
        print("⚠️ DeepAI caption generation error:", e)
        return []


# ---------- MAIN ENTRY ----------
def suggest_captions(prompt: str, template_name: Optional[str] = None) -> List[str]:
    """
    Generates multiple caption ideas using:
    1️⃣ OpenAI GPT-4o-mini (paid, primary)
    2️⃣ HuggingFace GPT-2 API
    3️⃣ DeepAI Text Generator
    4️⃣ Local GPT-2 (final fallback)
    """
    context = prompt if not template_name else f"{prompt} ({template_name})"
    ideas: List[str] = []

    # 1️⃣ OpenAI GPT-4o-mini
    ideas += _openai_generate(context, n=3)

    # 2️⃣ HuggingFace & DeepAI free APIs
    if len(ideas) < 3:
        ideas += _hf_inference(context, n=3)
        ideas += _deepai(context)

    # 3️⃣ Local fallback GPT-2
    if len(ideas) < 3:
        ideas += _local_generate(context, n=3)

    # ---------- Cleanup ----------
    uniq = []
    seen = set()
    for s in ideas:
        s = s.strip()
        if not s:
            continue
        if s not in seen:
            seen.add(s)
            uniq.append(s)

    # ---------- Guaranteed fallback phrases ----------
    if len(uniq) < 3:
        seed = prompt.strip().capitalize() or "Something"
        uniq += [
            f"{seed} // But make it meme",
            f"When {seed} hits",
            f"POV: {seed}"
        ]

    return uniq[:5]


def plan_from_context(context: str):
    """
    Returns {"image_prompt": str, "captions": [str,...]} using OpenAI planner.
    Falls back to local caption suggester if something goes wrong.
    """
    try:
        return openai_plan_from_context(context)
    except Exception as e:
        print("⚠️ Planner failed, falling back:", e)
        return {
            "image_prompt": "Generate a neutral, abstract background with top/bottom space.",
            "captions": suggest_captions(context)  # existing function
        }
