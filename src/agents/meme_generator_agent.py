from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx, io, time
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote
import requests


app = FastAPI(title="Meme Generation Agent", version="2.1")

@app.get("/meme-generator")
async def meme_generator_status():
    return {"status": "ok", "agent": "meme_generator"}

class GenReq(BaseModel):
    template_id: str
    top_text: str = ""
    bottom_text: str = ""
    backend: str | None = None
    template_url: str | None = None


async def _gen_imgflip(req: GenReq) -> dict | None:
    if not req.template_id.isdigit():
        return None
    payload = {
        "template_id": req.template_id,
        "username": IMGFLIP_USER,
        "password": IMGFLIP_PASS,
        "text0": req.top_text,
        "text1": req.bottom_text,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        j = (await client.post("https://api.imgflip.com/caption_image", data=payload)).json()
    if j.get("success") and j.get("data", {}).get("url"):
        return {"meme_url": j["data"]["url"]}
    return None


async def _gen_memegen(req: GenReq) -> dict | None:
    tid = req.template_id
    if not (tid.startswith("memegen:") or tid.startswith("memegen_ex:")):
        return None

    def fmt(s: str) -> str:
        s = (s or "").strip() or "_"
        return quote(s, safe="").replace("%20", "_")

    if tid.startswith("memegen:"):
        slug = tid.split(":", 1)[1]
        url = f"https://api.memegen.link/images/{slug}/{fmt(req.top_text)}/{fmt(req.bottom_text)}.png"
    else:
        bg = tid.split(":", 1)[1]
        url = f"https://api.memegen.link/images/custom/{fmt(req.top_text)}/{fmt(req.bottom_text)}.png?background={quote(bg, safe='')}"
    return {"meme_url": url}
TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def list_templates() -> list[str]:
    return [str(p) for p in sorted(TEMPLATES_DIR.glob("*.jpg"))]

def pick_template(topic: str) -> str:
    # Simple heuristic: choose template by keyword
    topic_low = (topic or "").lower()
    mapping = {
        "choice": "drake.jpg",
        "approve": "drake.jpg",
        "distract": "distracted.jpg",
        "compare": "distracted.jpg",
        "study": "study.jpg",
        "work": "study.jpg",
    }
    for k, v in mapping.items():
        if k in topic_low:
            return str(TEMPLATES_DIR / v)
    # fallback to first
    templates = list_templates()
    return templates[0] if templates else ""

def score_caption(c: Dict[str, str]) -> float:
    # Very simple scoring: prefer medium length and some balance
    t = c["top"]
    b = c["bottom"]

    def word_count(s): 
        return max(1, len(s.split()))

    tl = word_count(t)
    bl = word_count(b)
    length_score = math.exp(-((tl-6)**2 + (bl-6)**2) / 20)  # peak near ~6 words each
    diversity = 1.0 if t.strip().lower() != b.strip().lower() else 0.5
    return length_score * diversity

def generate_meme(topic: str, model_name: str | None = None) -> str:
    cap = Captioner(model_name=model_name)
    candidates = cap.generate(topic, n=4)
    candidates.sort(key=score_caption, reverse=True)
    best = candidates[0]
    template = pick_template(topic)
    out_path = OUTPUT_DIR / f"meme_{topic.replace(' ', '_')}.jpg"
    render_meme(template, best["top"], best["bottom"], str(out_path))
    return str(out_path)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", type=str, required=True, help="Meme topic, e.g., 'deadline at 5pm'")
    ap.add_argument("--model", type=str, default=None, help="Optional HF model name for captions")
    args = ap.parse_args()

    out = generate_meme(args.topic, model_name=args.model)
    print(f"Saved: {out}")
