# app/api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import get_answer_from_documents_v1, get_answer_from_documents_v2, get_answer_from_documents_v3
from app.services.user_service import get_or_create_user
from app.db.session import get_db

router = APIRouter(tags=["chat"])

@router.post("/chat/v1", response_model=ChatResponse, summary="Chat với chatbot v1 (trả lời tiếng Việt)")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Nhận message (tiếng Việt) từ user, trả về câu trả lời.
    Kết quả được truy xuất từ dữ liệu huấn luyện (FAISS + Document).
    Tốc độ nhanh, câu trả lời có thể sẽ thô
    Lưu ý: không cần GPU, chỉ cần CPU.
    """
    user_id = request.user_id
    answer = get_answer_from_documents_v1(user_id, request.message, db)
    return {"answer": answer}

@router.post("/chat/v2", response_model=ChatResponse, summary="Chat với chatbot v2 (trả lời tiếng Việt)")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Nhận message (tiếng Việt) từ user, trả về câu trả lời.
    Kết quả được truy xuất từ dữ liệu huấn luyện (FAISS + Document). 
    Kết quả sơ ban đầu được xử lý qua LLM để có câu trả lời tự nhiên.
    Tốc độ có thể chậm hơn một chút so với chat_v1.
    Lưu ý: Có thể sử dụng GPU để tăng tốc độ.
    """
    user_id = request.user_id
    answer = get_answer_from_documents_v2(user_id, request.message, db)
    return {"answer": answer}

@router.post("/chat/v3", response_model=ChatResponse, summary="Chat với chatbot v3 (trả lời tiếng Việt)")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Nhận message (tiếng Việt) từ user, trả về câu trả lời.
    Kết quả được truy xuất thẳng từ dữ liệu đã fine-tune để có câu trả lời tự nhiên.
    Tốc độ có thể chậm hơn một chút so với chat_v1.
    Lưu ý: Có thể sử dụng GPU để tăng tốc độ.
    """
    user_id = request.user_id
    answer = get_answer_from_documents_v3(user_id, request.message, db)
    return {"answer": answer}
