from pydantic import BaseModel
from datetime import datetime
from typing import List

class UnknownQuestionOut(BaseModel):
    id: int
    question: str
    timestamp: datetime

    class Config:
        orm_mode = True

class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int

class UnknownQuestionResponse(BaseModel):
    items: List[UnknownQuestionOut]
    pagination: PaginationInfo