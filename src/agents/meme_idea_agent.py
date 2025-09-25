from fastapi import FastAPI
import httpx
import itertools

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
    return {"status": "ok", "agent": "meme_idea", "sources": len(SOURCES)}


async def _get_from_source(idx: int):
    name, url = SOURCES[idx]
    headers = {}
    if name == "icanhazdadjoke":
        headers["Accept"] = "application/json"

    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        try:
            j = r.json()
        except Exception:
            j = None

        if name == "JokeAPI" and j:
            return j.get("joke") or None
        if name == "icanhazdadjoke" and j:
            return j.get("joke") or None
        if name == "Quotable" and j:
            return j.get("content") or None
        if name == "ZenQuotes" and isinstance(j, list) and j:
            return j[0].get("q") or None
        if name == "AdviceSlip" and j:
            slip = j.get("slip") or {}
            return slip.get("advice") or None

    return None
