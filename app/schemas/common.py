from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int

class PaginationResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationInfo