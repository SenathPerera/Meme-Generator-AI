from pathlib import Path
from typing import List

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)