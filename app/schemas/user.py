# app/schemas/user.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: Optional[str]

class UserOut(BaseModel):
    id: int
    name: Optional[str]

    class Config:
        orm_mode = True
