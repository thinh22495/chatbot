# app/api/v1/endpoints/train.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd

from app.schemas.document import DocumentOut
from app.services.document_service import create_documents_from_excel, delete_document, get_all_documents
from app.services.chat_service import rebuild_faiss_index
from app.db.session import SessionLocal, get_db

router = APIRouter(prefix="/train", tags=["train"])

@router.post("/upload", summary="Upload file Excel để thêm dữ liệu huấn luyện")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Vui lòng upload file Excel (.xlsx).")

    try:
        contents = await file.read()

        import io
        import pandas as pd
        df = pd.read_excel(io.BytesIO(contents), header=None)
    except Exception as e:
        print(f"Lỗi đọc file: {str(e)}")
        raise HTTPException(status_code=400, detail="Không thể đọc file Excel.")

    docs = create_documents_from_excel(df, db)
    return {"message": f"Đã thêm {len(docs)} bản ghi từ file Excel."}


@router.post("/start", summary="Xây dựng FAISS index từ dữ liệu đã upload")
def start_training(db: Session = Depends(get_db)):
    """
    Tạo chỉ mục FAISS dựa trên tất cả Document trong DB.
    """
    success = rebuild_faiss_index(db)
    if not success:
        raise HTTPException(status_code=400, detail="Không có dữ liệu để tạo index.")
    return {"message": "Đã tạo FAISS index cho các câu hỏi.", "documents": len(get_all_documents(db))}

@router.get("/documents", response_model=list[DocumentOut], summary="Danh sách tài liệu huấn luyện")
def list_documents(db: Session = Depends(get_db)):
    """
    Trả về danh sách các tài liệu (câu hỏi và hướng dẫn) đang có.
    """
    docs = get_all_documents(db)
    return docs

@router.delete("/{document_id}", summary="Xóa tài liệu huấn luyện theo ID")
def delete_document_endpoint(document_id: int, db: Session = Depends(get_db)):
    """
    Xoá tài liệu huấn luyện (Document) theo ID.
    Lưu ý: Sau khi xóa, có thể cần gọi lại /train/start để xây dựng lại index FAISS.
    """
    success = delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document không tồn tại.")
    # Có thể rebuild FAISS index ở đây hoặc yêu cầu client gọi lại /train/start.
    return {"message": f"Đã xoá document với id = {document_id}."}
