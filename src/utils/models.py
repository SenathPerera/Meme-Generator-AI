from pydantic import BaseModel
from typing import Dict

class SecureReq(BaseModel):
    action: str                     # idea | templates | search_templates | generate
    payload: Dict[str, str] = {}
