from sqlalchemy import Column, Integer, Text, DateTime
from app.db.base import Base
from datetime import datetime

class UnknownQuestion(Base):
    __tablename__ = "unknown_questions"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)