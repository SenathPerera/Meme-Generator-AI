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
