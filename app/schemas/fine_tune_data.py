# app/schemas/fine_tune_data.py
from pydantic import BaseModel

class FineTuneDataOut(BaseModel):
    id: int
    answer: str
    target: str

    class Config:
        orm_mode = True
