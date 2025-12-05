from typing import Dict, List

# Lightweight Grok pipeline shim.
# Assumes a function `generate_with_grok(context: str) -> Dict` may exist elsewhere.
# Falls back to a simple local planner structure if that import is unavailable.


def _fallback_plan(context: str) -> Dict:
    try:
        # Reuse existing local caption suggester for fallback shape
        from src.agents.meme_idea_agent import suggest_captions
        captions: List[str] = suggest_captions(context)
    except Exception:
        captions = [
            f"{context.strip().capitalize() or 'This'} // make it meme",
            "POV: chaos",
            "When it escalates",
        ]
    return {
        "image_prompt": "Generate an edgy/uncensored memeable background with clear top and bottom space for text.",
        "captions": captions,
    }


def plan_from_context(context: str) -> Dict:
    """
    Return a Grok-style plan: {"image_prompt": str, "captions": [str, ...]}.
    If an external `generate_with_grok` is available, use it. Otherwise, fallback.
    """
    try:
        # Optional external integration point
        from src.grok_pipeline_client import generate_with_grok  # type: ignore
        return generate_with_grok(context)
    except Exception as e:
        print("[grok] plan_from_context fallback:", e)
        return _fallback_plan(context)
