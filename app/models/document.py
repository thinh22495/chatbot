# app/models/document.py
from sqlalchemy import Column, Integer, Text
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)   # Câu hỏi (đầu vào từ Excel)
    answer = Column(Text, nullable=False)     # Hướng dẫn/đáp án tương ứng
