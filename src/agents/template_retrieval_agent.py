from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import List, Dict
import httpx
import asyncio
import time
from rapidfuzz import process, fuzz

app = FastAPI(title="Template Retrieval Agent", version="2.0")

# Unified cache across sources
TEMPLATES: List[Dict] = []
_LAST_LOAD = 0.0
_CACHE_TTL = 60 * 30


IMGFLIP_URL = "https://api.imgflip.com/get_memes"
REDDIT_URL = "https://www.reddit.com/r/memes.json?limit=50"
MEMEGEN_TEMPLATES = "https://api.memegen.link/templates/"
MEMEGEN_EXAMPLES = "https://api.memegen.link/images/"
STATIC_FALLBACK = [
    {"id": "61579", "name": "One Does Not Simply",
        "url": "https://i.imgflip.com/1bij.jpg"},
    {"id": "112126428", "name": "Distracted Boyfriend",
        "url": "https://i.imgflip.com/1ur9b0.jpg"},
    {"id": "181913649", "name": "Drake Hotline Bling",
        "url": "https://i.imgflip.com/30b1gx.jpg"},
]


def _dedupe(templates: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for t in templates:
        key = (t.get("id") or t.get("url"))
        if key and key not in seen:
            seen.add(key)
            out.append(t)
    return out


async def _load_imgflip() -> List[Dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(IMGFLIP_URL)
        j = r.json()
    if j.get("success"):
        return [{"id": m["id"], "name": m["name"], "url": m["url"]} for m in j["data"]["memes"]]
    return []


async def _load_reddit() -> List[Dict]:
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as client:
        r = await client.get(REDDIT_URL)
        j = r.json()
    out = []
    for c in j.get("data", {}).get("children", []):
        d = c.get("data", {})
        url = d.get("url_overridden_by_dest") or d.get("url")
        title = d.get("title")
        if url and title and (url.endswith(".jpg") or url.endswith(".png") or "i.redd.it" in url):
            out.append(
                {"id": url, "name": f"Reddit: {title[:60]}", "url": url})
    return out


async def _load_memegen_templates() -> List[Dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(MEMEGEN_TEMPLATES)
        j = r.json()
    out = []
    for t in j:
        if "blank" in t and "name" in t and "id" in t:
            out.append(
                {"id": f"memegen:{t['id']}", "name": t["name"], "url": t["blank"]})
    return out
