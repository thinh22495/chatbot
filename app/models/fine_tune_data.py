# app/models/fine_tune_data.py
from sqlalchemy import Column, Integer, Text
from app.db.base import Base

class FineTuneData(Base):
    __tablename__ = "fine_tune_data"
    id = Column(Integer, primary_key=True, index=True)
    answer = Column(Text, nullable=False)   # Câu trả lời (đầu vào từ Excel)
    target = Column(Text, nullable=False)   # Câu trả lời theo nhiều ngữ cảnh khác nhau
