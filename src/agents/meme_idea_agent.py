
import itertools
import httpx
from fastapi.responses import JSONResponse








from fastapi import FastAPI

app = FastAPI(title="Meme Idea Agent", version="2.0")

SOURCES = [
    ("JokeAPI", "https://v2.jokeapi.dev/joke/Any?safe-mode&type=single"),
    ("icanhazdadjoke", "https://icanhazdadjoke.com/"),
    ("Quotable", "https://api.quotable.io/random"),
    ("ZenQuotes", "https://zenquotes.io/api/random"),
    ("AdviceSlip", "https://api.adviceslip.com/advice"),
]
_cycle = itertools.cycle(range(len(SOURCES)))

@app.get("/meme-generator")
async def meme_generator_status():
    return {"status": "ok", "agent": "meme_idea", "sources": len(SOURCES)}  # SOURCES added in next commit

async def _get_from_source(idx: int) -> str | None:
    name, url = SOURCES[idx]
    headers = {}
    if name == "icanhazdadjoke":
        headers["Accept"] = "application/json"

    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        j = r.json() if "application/json" in r.headers.get("Content-Type","").lower() else None

        if name == "JokeAPI":
            if j and j.get("type") == "single" and j.get("joke"):
                return j["joke"]
        elif name == "icanhazdadjoke":
            if j and j.get("joke"):
                return j["joke"]
        elif name == "Quotable":
            if j and j.get("content"):
                return j["content"]
        elif name == "ZenQuotes":
            if isinstance(j, list) and j and "q" in j[0]:
                return j[0]["q"]
        elif name == "AdviceSlip":
            if j and j.get("slip", {}).get("advice"):
                return j["slip"]["advice"]
    return None

@app.get("/get_idea")
async def get_idea():
    """
    Tries up to 5 sources in rotating order. Returns the first success.
    """
    start_idx = next(_cycle)
    tries = list((start_idx + i) % len(SOURCES) for i in range(len(SOURCES)))
    for idx in tries:
        try:
            idea = await _get_from_source(idx)
            if idea:
                return {"source": SOURCES[idx][0], "idea": idea}
        except Exception:
            continue

    # fallback
    return JSONResponse(
        {"source": "fallback", "idea": "When the bug disappears right as the lecturer arrives."},
        status_code=200,
    )






