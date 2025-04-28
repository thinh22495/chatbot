# app/api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import get_answer_from_documents
from app.services.user_service import get_or_create_user
from app.db.session import get_db

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse, summary="Chat với chatbot (trả lời tiếng Việt)")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Nhận message (tiếng Việt) từ user, trả về câu trả lời.
    Lưu ý: Kết quả được truy xuất từ dữ liệu huấn luyện (FAISS + Document).
    """
    user_id = request.user_id
    # Nếu có user_id, tạo hoặc lấy user từ DB
    if user_id is not None:
        user = get_or_create_user(user_id, db)
        user_id = user.id
    answer = get_answer_from_documents(user_id, request.message, db)
    return {"answer": answer}
