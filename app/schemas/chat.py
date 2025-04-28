# app/schemas/chat.py
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    user_id: Optional[int] = None
    message: str

class ChatResponse(BaseModel):
    answer: str
