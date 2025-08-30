from pathlib import Path
from typing import List

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