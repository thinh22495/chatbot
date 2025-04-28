# app/services/user_service.py
from sqlalchemy.orm import Session
from app.models.user import User

def get_or_create_user(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user
    # Nếu user_id không tồn tại, tạo mới (ở đây chỉ đơn giản, bạn có thể tùy chỉnh)
    new_user = User(id=user_id, name=None)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
