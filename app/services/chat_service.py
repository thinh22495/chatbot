# app/services/chat_service.py
from sqlalchemy.orm import Session
import faiss
import numpy as np
from app.services.user_service import get_or_create_user
from app.models.chat_history import ChatHistory
from app.models.document import Document
from datetime import datetime

# Khởi tạo mô hình embedding PhoBERT (có thể thực hiện 1 lần khi module được load)
from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer('dangvantuan/vietnamese-embedding')  # mô hình embedding tiếng Việt&#8203;:contentReference[oaicite:2]{index=2}

# Đường dẫn file lưu FAISS index và mapping
INDEX_FILE = "data/faiss_index/faiss.index"
MAPPING_FILE = "data/faiss_index/mapping.pkl"

import pickle
# Hàm load index và mapping nếu đã tạo trước đó
def load_faiss_index():
    try:
        index = faiss.read_index(INDEX_FILE)
        with open(MAPPING_FILE, 'rb') as f:
            id_map = pickle.load(f)
        return index, id_map
    except Exception as e:
        return None, None

# Thư mục chứa FAISS index
faiss_index, faiss_id_map = load_faiss_index()

def rebuild_faiss_index(db: Session):
    """
    Tạo lại FAISS index từ tất cả Document trong DB.
    Lưu index ra file và lưu mapping id.
    """
    docs = db.query(Document).all()
    texts = [doc.question for doc in docs]
    ids = [doc.id for doc in docs]
    if not texts:
        return False

    # Tạo vectors bằng mô hình embedding PhoBERT
    vectors = embed_model.encode(texts, convert_to_numpy=True)
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors.astype('float32'))

    # Lưu index và mapping
    faiss.write_index(index, INDEX_FILE)
    with open(MAPPING_FILE, 'wb') as f:
        pickle.dump(ids, f)
    return True

def get_answer_from_documents(user_id: int, message: str, db: Session):
    global faiss_index, faiss_id_map

    # BỔ SUNG: Prompt HƯỚNG DẪN
    PROMPT_PREFIX = (
        "Bạn là trợ lý phần mềm giáo dục. "
        "Hãy trả lời chính xác, lịch sự bằng tiếng Việt. "
        "Câu hỏi: "
    )

    try:
        # Ghép prompt vào trước câu hỏi người dùng
        final_message = PROMPT_PREFIX + message

        if faiss_index is None or faiss_id_map is None:
            success = rebuild_faiss_index(db)
            if not success:
                return "Chưa có dữ liệu được đào tạo liên quan câu hỏi của bạn. Vui lòng hỏi lại sau khi tôi được cập nhật thêm!"
            faiss_index, faiss_id_map = load_faiss_index()

        # Encode câu hỏi sau khi gắn prompt
        query_vec = embed_model.encode([final_message], convert_to_numpy=True)
        k = 3
        D, I = faiss_index.search(query_vec.astype('float32'), k)

        answer = ""
        for idx in I[0]:
            if idx < len(faiss_id_map):
                doc_id = faiss_id_map[idx]
                doc = db.query(Document).get(doc_id)
                if doc:
                    answer += f"- {doc.answer}\n"

        if not answer:
            answer = "Xin lỗi, tôi chưa có câu trả lời phù hợp."

        if user_id is not None:
            # Kiểm tra user_id tồn tại trong DB
            save_history = False
            if user_id is not None:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    save_history = True

            # Lưu lịch sử chat vào DB
            if save_history:
                history = ChatHistory(
                    user_id=user_id,
                    question=message,
                    answer=answer.strip(),
                    timestamp=datetime.utcnow()
                )
                db.add(history)
                db.commit()
    
        return answer.strip()
    except Exception as e:
        print(f"{str(e)}")
        return "Đã xảy ra lỗi khi tìm kiếm câu trả lời. Vui lòng thử lại sau."
    

