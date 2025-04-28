# app/schemas/document.py
from pydantic import BaseModel

class DocumentOut(BaseModel):
    id: int
    question: str
    answer: str

    class Config:
        orm_mode = True
