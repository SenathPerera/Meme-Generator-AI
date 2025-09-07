from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx, io, time, requests
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote



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


async def _gen_local(req: GenReq) -> dict | None:
    """
    Renders locally using Pillow. Requires a direct image URL.
    We prefer req.template_url; if absent, we accept template_id if it's already a URL.
    """
    url = req.template_url or req.template_id
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        return None

    # download image
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    w, h = img.size

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", size=max(24, w // 15))
    except Exception:
        font = ImageFont.load_default()

    def outline_text(x, y, text):
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2),(0,-2),(0,2),(-2,0),(2,0)]:
            draw.text((x + dx, y + dy), text, font=font, fill="black")
        draw.text((x, y), text, font=font, fill="white")

    if req.top_text:
        tw, th = draw.textbbox((0, 0), req.top_text, font=font)[2:]
        outline_text((w - tw) // 2, 10, req.top_text)

    if req.bottom_text:
        bw, bh = draw.textbbox((0, 0), req.bottom_text, font=font)[2:]
        outline_text((w - bw) // 2, h - bh - 10, req.bottom_text)

    ts = int(time.time())
    fname = GENERATED_DIR / f"meme_{ts}.jpg"
    img.save(fname, format="JPEG", quality=92)

    # Optional upload to Imgur
    if IMGUR_CLIENT_ID:
        try:
            with open(fname, "rb") as f:
                resp = requests.post(
                    "https://api.imgur.com/3/image",
                    headers={"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"},
                    files={"image": f},
                    timeoiut=30,
                ).json()
            if resp.get("success") and resp.get("data", {}).get("link"):
                return {"meme_url": resp["data"]["link"]}
        except Expection:
            pass

    return {"meme_url": f"file://{fname.as_posix()}"}

@app.post("/generate_meme")
async def generate_meme(req: GenReq):
    """
    Tries backends in order (or force via req.backend):
      1) Imgflip (numeric template_id)
      2) Memegen.link (template_id 'memegen:<slug>' or 'memegen_ex:<url>')
      3) Local Pillow (template_url or URL template_id)
    """
    order = ["imgflip", "memegen", "local"] if not req.backend else [req.backend]

    for backend in order:
        try:
            if backend == "imgflip":
                res = await _gen_imgflip(req)
            elif backend == "memegen":
                res = await _gen_memegen(req)
            elif backend == "local":
                res = await _gen_local(req)
            else:
                res = None
            if res and res.get("meme_url"):
                return res
        except Exception:
            continue

    return JSONResponse({"error": "All backends failed"}, status_code=502)

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
