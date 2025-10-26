import os, requests, re, csv, datetime
from dataclasses import dataclass
from src.utils.config import (
    COMPLIANCE_LOG,
    BANNED_WORDS_FILE,
    PERSPECTIVE_API_KEY,
    HUGGINGFACE_API_TOKEN,
)
from src.utils.openai_client import openai_moderate


