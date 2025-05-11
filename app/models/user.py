# app/models/user.py
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # Bạn có thể thêm các trường khác như username, email nếu cần
    name = Column(String, nullable=True)
