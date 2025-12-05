import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import textwrap, urllib.parse
import urllib.request

from src.utils.config import FONT_PATH, USE_PAID_API, OPENAI_API_KEY
from src.utils.openai_client import openai_image
from src.utils.telemetry import set_last_image_provider  # NEW
import os, tempfile

from io import BytesIO
import os



def _encode(text: str) -> str:
    return urllib.parse.quote((text or "_").strip(), safe="")


# ---------------- Emoji-aware text rendering helpers ----------------
def _load_font(base_width: int, scale: float = 0.08):
    size = max(12, int(base_width * scale))
    candidates = [
        FONT_PATH,
        "src/data/fonts/impact.ttf",
        "src/data/fonts/Impact.ttf",
        "impact.ttf",
        "Impact.ttf",
        "arial.ttf",
        "DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    # As last resort
    return ImageFont.load_default()


def _load_emoji_font(base_width: int, scale: float = 0.08):
    size = max(12, int(base_width * scale))
    candidates = [
        r"C:\\Windows\\Fonts\\seguiemj.ttf",
        r"C:\\Windows\\Fonts\\seguisym.ttf",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "src/data/fonts/NotoColorEmoji.ttf",
        "src/data/fonts/NotoEmoji-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return None


_emoji_regex = re.compile("[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF\U0001F1E6-\U0001F1FF]")


def _split_runs_by_emoji(text: str):
    runs = []
    if not text:
        return runs
    curr = []
    curr_is_emoji = bool(_emoji_regex.match(text[0]))
    for ch in text:
        is_em = bool(_emoji_regex.match(ch))
        if is_em != curr_is_emoji:
            runs.append((curr_is_emoji, "".join(curr)))
            curr = [ch]
            curr_is_emoji = is_em
        else:
            curr.append(ch)
    if curr:
        runs.append((curr_is_emoji, "".join(curr)))
    return runs


def _line_length_mixed(draw: ImageDraw.ImageDraw, text: str, font_main, font_emoji) -> int:
    total = 0
    runs = _split_runs_by_emoji(text)
    for is_emoji, seg in runs:
        f = (font_emoji or font_main) if is_emoji else font_main
        total += int(draw.textlength(seg, font=f))
    return total


def _textlength_mixed(draw: ImageDraw.ImageDraw, text: str, font_main, font_emoji) -> int:
    if not text:
        return 0
    lines = text.split("\n")
    if len(lines) > 1:
        return max(_line_length_mixed(draw, ln, font_main, font_emoji) for ln in lines)
    return _line_length_mixed(draw, text, font_main, font_emoji)


def _twemoji_filename_for(grapheme: str) -> str:
    cps = '-'.join([format(ord(ch), 'x') for ch in grapheme])
    return cps + '.png'


def _try_paste_emoji(image, xy, text, font_main) -> int:
    from pathlib import Path as _P
    x, y = xy
    size = getattr(font_main, 'size', 32)
    p = _P('src/data/emoji') / _twemoji_filename_for(text)
    if not p.exists():
        return 0
    try:
        im = Image.open(str(p)).convert('RGBA').resize((size, size), Image.LANCZOS)
        image.paste(im, (x, y - int(size*0.8)), im)
        return size
    except Exception:
        return 0


def _draw_text_with_outline_mixed(image, draw, xy, text, font_main, font_emoji, align="left"):
    x, y = xy
    runs = _split_runs_by_emoji(text)
    for is_emoji, seg in runs:
        f = (font_emoji or font_main) if is_emoji else font_main
        if is_emoji:
            pasted = _try_paste_emoji(image, (x, y), seg, font_main)
            if pasted > 0:
                seg_w = pasted
                x += seg_w
                continue
        seg_w = int(draw.textlength(seg, font=f))
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), seg, font=f, fill="black", align=align)
        draw.text((x, y), seg, font=f, fill="white", align=align)
        x += seg_w


def _draw_multiline_with_outline_mixed(image, draw, xy, text, font_main, font_emoji, align="left", block_width=None, line_gap=6):
    x, y = xy
    lines = text.split("\n")
    if block_width is None:
        block_width = max(_line_length_mixed(draw, ln, font_main, font_emoji) for ln in lines)
    # approximate line height
    try:
        ascent, descent = font_main.getmetrics()
        line_h = ascent + descent
    except Exception:
        line_h = int(font_main.size * 1.2) if hasattr(font_main, "size") else 24
    for ln in lines:
        lw = _line_length_mixed(draw, ln, font_main, font_emoji)
        if align == "center":
            lx = x + (block_width - lw) // 2
        elif align == "right":
            lx = x + (block_width - lw)
        else:
            lx = x
        _draw_text_with_outline_mixed(image, draw, (lx, y), ln, font_main, font_emoji, align=align)
        y += line_h + line_gap

def generate_with_memegen(template_id: str, top: str, bottom: str, out_path: str) -> str:
    url = f"https://api.memegen.link/images/{template_id}/{_encode(top)}/{_encode(bottom)}.png"
    r = requests.get(url, timeout=20)
    if not r.ok:
        raise RuntimeError("Memegen API failed")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(r.content)
    set_last_image_provider("memegen")
    print("🧩 Used Memegen fallback")
    return out_path



def generate_with_pillow(template_url: str, caption: str, out_path: str) -> str:
    img = Image.open(requests.get(template_url, stream=True, timeout=20).raw).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Robust truetype loading with fallbacks + emoji support
    font = _load_font(W, 0.08)
    emoji_font = _load_emoji_font(W, 0.08)

    parts = [p.strip() for p in caption.split("//")]
    if len(parts) == 1:
        parts = ["", parts[0]]

    if parts[0]:
        t = textwrap.fill(parts[0].upper(), width=16)
        tw = _textlength_mixed(draw, t, font, emoji_font)
        _draw_multiline_with_outline_mixed(img, draw, ((W - tw) // 2, int(H * 0.05)), t, font, emoji_font, align="center", block_width=tw)

    btxt = textwrap.fill(parts[1].upper(), width=16)
    bw = _textlength_mixed(draw, btxt, font, emoji_font)
    _draw_multiline_with_outline_mixed(img, draw, ((W - bw) // 2, H - int(H * 0.25)), btxt, font, emoji_font, align="center", block_width=bw)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG")
    set_last_image_provider("pillow")
    print("🖍️ Used Pillow overlay fallback")
    return out_path


def overlay_text_on_local_image(image_path: str, caption: str, out_path: str) -> str:
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Keep overlay consistent with Pillow renderer + emoji support
    font = _load_font(W, 0.08)
    emoji_font = _load_emoji_font(W, 0.08)

    parts = [p.strip() for p in caption.split("//")]
    if len(parts) == 1:
        parts = ["", parts[0]]

    if parts[0]:
        t = textwrap.fill(parts[0].upper(), width=16)
        tw = _textlength_mixed(draw, t, font, emoji_font)
        _draw_text_with_outline_mixed(draw, ((W - tw) // 2, int(H * 0.05)), t, font, emoji_font, align="center")

    btxt = textwrap.fill(parts[1].upper(), width=16)
    bw = _textlength_mixed(draw, btxt, font, emoji_font)
    _draw_text_with_outline_mixed(draw, ((W - bw) // 2, H - int(H * 0.25)), btxt, font, emoji_font, align="center")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG")
    print("🖍️ Overlayed caption onto OpenAI background")
    return out_path


def generate_meme(template: dict, caption: str, out_path: str) -> str:
    top, bottom = ("", caption.strip())
    if "//" in caption:
        parts = [p.strip() for p in caption.split("//", 1)]
        top, bottom = parts[0], parts[1]

    # Prefer drawing directly on the provided template URL (bigger, local font)
    if template.get("url"):
        try:
            return generate_with_pillow(template["url"], caption, out_path)
        except Exception:
            pass

    # Do not use Memegen for previews; keep a consistent font via Pillow

    if USE_PAID_API and OPENAI_API_KEY:
        try:
            base = template.get("url", "")
            tname = template.get("name", template.get("id", "template"))
            prompt = (
                f"Create a meme-style image (no NSFW) inspired by '{tname}'. "
                f"Use a classic meme vibe similar to {base if base else 'popular meme formats'}. "
                f"Place space for TOP and BOTTOM text (do not add any text)."
            )
            # ^ Notice: we do NOT put the actual caption into the prompt.
            print("🖼️ Using OpenAI image generation (background-only)")
            tmp_bg = os.path.join(tempfile.gettempdir(), "meme_bg_openai.png")
            path_bg = openai_image(prompt, out_path=tmp_bg)
            set_last_image_provider("openai")
            # Now overlay the caption locally
            return overlay_text_on_local_image(path_bg, caption, out_path)
        except Exception as e:
            msg = str(e)
            print("⚠️ OpenAI image generation failed, falling back:", msg)

    # Do not use Memegen as a late fallback

    return generate_with_pillow(template.get("url", ""), caption, out_path)


def generate_from_prompt_and_caption(image_prompt: str, caption: str, out_path: str) -> str:
    """
    Uses OpenAI Images to create a safe background from image_prompt,
    then overlays 'caption' locally. Falls back to Memegen/Pillow if needed.
    """
    if USE_PAID_API and OPENAI_API_KEY:
        try:
            print("🖼️ Using OpenAI image generation (planner prompt)")
            tmp_bg = os.path.join(tempfile.gettempdir(), "meme_bg_openai.png")
            path_bg = openai_image(image_prompt, out_path=tmp_bg)
            set_last_image_provider("openai")
            return overlay_text_on_local_image(path_bg, caption, out_path)
        except Exception as e:
            print("⚠️ OpenAI image generation failed, falling back:", e)

    # Fall back to plain Pillow if OpenAI fails and no template is provided here.
    return generate_with_pillow("https://picsum.photos/1200/1200", caption, out_path)

def _impact_font(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def _draw_text_box(draw, W, H, box, font):
    text = (box.get("text") or "").strip()
    if not text:
        return
    if box.get("uppercase", True):
        text = text.upper()

    max_width_px = max(16, int((box.get("width", 0.8) or 0.8) * W))
    align = box.get("align", "center")
    # wrap
    words = text.split()
    lines = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width_px:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    block = "\n".join(lines)

    bbox = draw.multiline_textbbox((0, 0), block, font=font, align=align)
    bw = bbox[2] - bbox[0]

    x = int((box.get("x", 0.1) or 0.1) * W)
    y = int((box.get("y", 0.1) or 0.1) * H)

    # align within the max-width region
    if align == "center":
        x = int(x + (max_width_px - bw) / 2)
    elif align == "right":
        x = int(x + (max_width_px - bw))

    # outline + fill
    def draw_with_outline(xy):
        ox, oy = xy
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx == 0 and dy == 0:
                    continue
                draw.multiline_text((ox+dx, oy+dy), block, font=font, fill="black", align=align, spacing=4)
        draw.multiline_text((ox, oy), block, font=font, fill="white", align=align, spacing=4)

    draw_with_outline((x, y))

# Path for local font
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests

font_path = "src/data/fonts/impact.ttf"

def render_layout_on_template(template: dict, boxes: list, out_path: str) -> str:
    # Load the template image from URL
    image_url = template["url"]
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Render each text box
    for box in boxes:
        text = box["text"].upper() if box.get("uppercase", True) else box["text"]
        font_scale = box.get("font_scale", 0.06)
        box_width = int(width * box["width"])
        x = int(box["x"] * width)
        y = int(box["y"] * height)
        align = box.get("align", "center")

        # Estimate font size
        font_size = max(int(width * font_scale), 12)
        font = ImageFont.truetype(font_path, font_size)
        emoji_font = _load_emoji_font(width, font_scale)

        # Wrap text to fit inside box width
        def wrap_text(text, font, max_width):
            words = text.split()
            lines = []
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                text_width = draw.textbbox((0, 0), test_line, font=font)[2]
                if text_width <= max_width:
                    line = test_line
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)
            return lines

        lines = wrap_text(text, font, box_width)

        # Draw each line with alignment and stroke (emoji aware)
        line_spacing = font_size + 6
        for i, line in enumerate(lines):
            text_width = _textlength_mixed(draw, line, font, emoji_font)
            line_x = x
            if align == "center":
                line_x = x + (box_width - text_width) // 2
            elif align == "right":
                line_x = x + (box_width - text_width)

            line_y = y + i * line_spacing
            _draw_text_with_outline_mixed(image, draw, (line_x, line_y), line, font, emoji_font, align=align)

    # Save and return
    image.save(out_path)
    return out_path


def draw_text_on_image(image_path, top_text, bottom_text):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Adjust font size based on image width
    font_size = int(width / 15)
    font = ImageFont.truetype("arial.ttf", font_size)  # Or use any .ttf font you have

    # Top text
    if top_text:
        top_text = top_text.upper()
        top_w, top_h = draw.textsize(top_text, font=font)
        draw.text(((width - top_w) / 2, 10), top_text, font=font, fill='white', stroke_width=2, stroke_fill='black')

    # Bottom text
    if bottom_text:
        bottom_text = bottom_text.upper()
        bottom_w, bottom_h = draw.textsize(bottom_text, font=font)
        draw.text(((width - bottom_w) / 2, height - bottom_h - 10), bottom_text, font=font, fill='white', stroke_width=2, stroke_fill='black')

    return img

def draw_text(draw, text, width, y_pos):
    font_size = int(width / 15)
    font = ImageFont.truetype("arial.ttf", font_size)
    w, h = draw.textsize(text, font=font)
    draw.text(((width - w) / 2, y_pos), text, font=font, fill="white", stroke_width=2, stroke_fill="black")
