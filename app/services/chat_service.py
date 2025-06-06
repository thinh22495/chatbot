# app/services/chat_service.py
from sqlalchemy.orm import Session
import faiss
import numpy as np
from app.services.user_service import get_or_create_user
from app.models.chat_history import ChatHistory
from app.models.document import Document
from app.models.user import User
from app.models.fine_tune_data import FineTuneData
from app.models.unknown_question import UnknownQuestion
from datetime import datetime
import pickle
import torch
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from pathlib import Path

# Đường dẫn file lưu FAISS index và mapping
INDEX_FILE = "data/faiss_index/faiss.index"
MAPPING_FILE = "data/faiss_index/mapping.pkl"

# Đường dẫn file lưu dư liệu fine-tune
FINE_TUNE_FILE = "data/fine_tune/"

# Khởi tạo mô hình embedding (có thể thực hiện 1 lần khi module được load)
from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer('VoVanPhuc/sup-SimCSE-VietNamese-phobert-base')

# Khởi tạo mô hình (ưu tiên load checkpoint fine-tune nếu có)
# from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq

if Path(FINE_TUNE_FILE).exists() and (Path(FINE_TUNE_FILE) / "pytorch_model.bin").exists():
    tokenizer = AutoTokenizer .from_pretrained(FINE_TUNE_FILE)
    model = AutoModelForSeq2SeqLM .from_pretrained(FINE_TUNE_FILE)
else:
    model_name = "VietAI/vit5-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

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
    Tự động nạp lại index sau khi rebuild.
    """
    global faiss_index, faiss_id_map

    try:
        docs = db.query(Document).all()
        texts = [doc.question for doc in docs]
        ids = [doc.id for doc in docs]
        if not texts:
            return False

        # Tạo vectors bằng mô hình embedding
        vectors = embed_model.encode(texts, convert_to_numpy=True)
        dim = vectors.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(vectors.astype('float32'))

        # Lưu index và mapping
        faiss.write_index(index, INDEX_FILE)
        with open(MAPPING_FILE, 'wb') as f:
            pickle.dump(ids, f)

        # Nạp lại index và mapping vào biến global
        faiss_index, faiss_id_map = load_faiss_index()
        
        return True
    except Exception as e:
        print(f"Lỗi quá trình faiss dữ liệu: {str(e)}")
        return False

def rebuild_fine_tune(db: Session):
    """
    Fine-tune mô hình ViT5-base với dữ liệu đã upload từ FineTuneData.
    Lưu checkpoint vào thư mục FINE_TUNE_FILE.
    """

    docs = db.query(FineTuneData).all()
    # Sử dụng trường 'answers' làm câu hỏi, 'target' làm câu trả lời theo ngữ cảnh
    questions = [doc.answer for doc in docs]
    targets = [doc.target for doc in docs]
    if not questions or not targets:
        return False

    global tokenizer, model

    # Chuẩn bị dataset cho Trainer
    class QADataset(torch.utils.data.Dataset):
        def __init__(self, questions, targets, tokenizer, max_length=256):
            self.questions = questions
            self.targets = targets
            self.tokenizer = tokenizer
            self.max_length = max_length

        def __len__(self):
            return len(self.questions)

        def __getitem__(self, idx):
            input_enc = self.tokenizer(
                self.questions[idx],
                truncation=True,
                padding="max_length",
                max_length=self.max_length,
                return_tensors="pt"
            )
            target_enc = self.tokenizer(
                self.targets[idx],
                truncation=True,
                padding="max_length",
                max_length=self.max_length,
                return_tensors="pt"
            )
            return {
                "input_ids": input_enc.input_ids.squeeze(),
                "attention_mask": input_enc.attention_mask.squeeze(),
                "labels": target_enc.input_ids.squeeze()
            }

    dataset = QADataset(questions, targets, tokenizer)

    # Thiết lập tham số huấn luyện
    training_args = TrainingArguments(
        output_dir=FINE_TUNE_FILE, # Thư mục lưu checkpoint sau khi fine-tune.
        num_train_epochs=3, #Số epoch huấn luyện (mặc định 1).
        per_device_train_batch_size=4, # Batch size cho mỗi thiết bị (mặc định 4).
        save_steps=10, #Lưu checkpoint sau mỗi số bước nhất định (mặc định 10).
        save_total_limit=2, # Số lượng checkpoint tối đa lưu trữ (mặc định 2).
        logging_steps=5, # Số bước giữa mỗi lần log (mặc định 5).
        learning_rate=5e-5, # Tốc độ học (mặc định 5e-5).
        remove_unused_columns=False, # Không loại bỏ các cột không dùng (để tránh lỗi với Trainer).
        report_to=[], # Không gửi log tới bất kỳ hệ thống nào (chạy offline).
        fp16=torch.cuda.is_available(), # Sử dụng FP16 nếu có GPU hỗ trợ.
        overwrite_output_dir=True # Ghi đè thư mục output nếu đã tồn tại.
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator,
        tokenizer=tokenizer
    )

    trainer.train()
    # Lưu checkpoint cuối cùng
    trainer.save_model(FINE_TUNE_FILE) # model.save_pretrained(FINE_TUNE_FILE)
    tokenizer.save_pretrained(FINE_TUNE_FILE)

    return True

def get_answer_from_documents_v1(user_id: int, message: str, db: Session):
    global faiss_index, faiss_id_map

    # Các ngưỡng khoảng cách
    THRESH_STRICT = 40
    THRESH_SUGGEST = 70

    try:
        query_vec = embed_model.encode([message], convert_to_numpy=True)
        k = 3
        D, I = faiss_index.search(query_vec.astype('float32'), k)

        # Trường hợp 1: Khớp hoàn toàn
        if D[0][0] < THRESH_STRICT:
            idx = I[0][0]
            doc_id = faiss_id_map[idx]
            doc = db.query(Document).get(doc_id)
            answer = doc.answer if doc else "Xin lỗi, tôi chưa có câu trả lời phù hợp."
        # Trường hợp 2: Khớp vừa phải
        elif D[0][0] < THRESH_SUGGEST:
            suggestions = []
            for idx in I[0]:
                if idx < len(faiss_id_map):
                    doc_id = faiss_id_map[idx]
                    doc = db.query(Document).get(doc_id)
                    if doc:
                        suggestions.append(doc.question)
            answer = (
                "Tôi chưa chắc chắn về câu hỏi của bạn. Bạn có muốn hỏi một trong các câu sau không?\n"
                + "\n".join(f"- {q}" for q in suggestions)
            )
            
            # Lưu câu hỏi chưa có câu trả lời chính xác
            unanswered = UnknownQuestion(
                question=message,
                timestamp=datetime.utcnow()
            )
            db.add(unanswered)
            
        # Trường hợp 3: Không phù hợp
        else:
            answer = "Chưa có dữ liệu được đào tạo liên quan câu hỏi của bạn. Vui lòng hỏi lại sau khi tôi được cập nhật thêm!"
            
            # Lưu câu hỏi chưa có câu trả lời
            unanswered = UnknownQuestion(
                question=message,
                timestamp=datetime.utcnow()
            )
            db.add(unanswered)

        # Lưu lịch sử chat
        if user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
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
    

def get_answer_from_documents_v2(user_id: int, message: str, db: Session):
    global faiss_index, faiss_id_map, tokenizer, model

    try:
        if faiss_index is None or faiss_id_map is None:
            success = rebuild_faiss_index(db)
            if not success:
                return "Chưa có dữ liệu được đào tạo liên quan câu hỏi của bạn. Vui lòng hỏi lại sau khi tôi được cập nhật thêm!"
            faiss_index, faiss_id_map = load_faiss_index()

        # Tìm kiếm top-1 kết quả phù hợp nhất
        query_vec = embed_model.encode([message], convert_to_numpy=True)
        k = 1
        D, I = faiss_index.search(query_vec.astype('float32'), k)

        answer = ""
        doc_context = None
        for idx in I[0]:
            if idx < len(faiss_id_map):
                doc_id = faiss_id_map[idx]
                doc = db.query(Document).get(doc_id)
                if doc:
                    doc_context = doc.answer
                    break

        if not doc_context:
            answer = "Xin lỗi, tôi chưa có câu trả lời phù hợp."
        else:
            # Sinh lại câu trả lời tự nhiên bằng ViT5 dựa trên câu hỏi và câu trả lời thô
            input_text = f"Câu hỏi: {message}\nCâu trả lời thô: {doc_context}\n Chỉ dựa vào câu trả lời thô được cung cấp, hãy diễn đạt lại câu trả lời cho tự nhiên:"
            input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=256, truncation=True)
            output_ids = model.generate(input_ids, max_length=128, num_beams=4, early_stopping=True)
            answer = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        # Lưu lịch sử chat nếu có user_id hợp lệ
        if user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
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
    
def get_answer_from_documents_v3(user_id: int, message: str, db: Session):
    global faiss_index, faiss_id_map, tokenizer, model
    try: 
        # Sử dụng dữ liệu fine-tune, tìm câu trả lời
        input_text = f"Câu hỏi: {message}\n Trả lời:"
        input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=256, truncation=True)
        output_ids = model.generate(input_ids, max_length=128, num_beams=4, early_stopping=True)
        answer = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        # Lưu lịch sử chat nếu có user_id hợp lệ
        if user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
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
