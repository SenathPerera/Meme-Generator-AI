
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
import httpx, re, time, csv, hashlib, asyncio
from pathlib import Path


app = FastAPI(title="Security & Compliance Agent", version="1.0")

# ---------- Models ----------
class SecureReq(BaseModel):
    action: str                     # idea | templates | search_templates | generate
    payload: Dict[str, str] = {}