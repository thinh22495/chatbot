# app/api/v1/endpoints/fine_tune.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd

from app.schemas.fine_tune_data import FineTuneDataOut
from app.services.fine_tune_data_service import create_documents_from_excel, delete_document, get_all_documents
from app.services.chat_service import rebuild_fine_tune
from app.db.session import SessionLocal, get_db

router = APIRouter(prefix="/fine_tune", tags=["Quản lý tài liệu fine-tune"])

@router.post("/upload", summary="Upload file Excel để thêm dữ liệu huấn luyện câu trả lời theo ngữ cảnh")
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

@router.post("/start", summary="Fine-tune từ dữ liệu đã upload")
def start_training(db: Session = Depends(get_db)):
    """
    Fine-tune dựa trên tất cả Document trong DB.
    """
    success = rebuild_fine_tune(db)
    if not success:
        raise HTTPException(status_code=400, detail="Không có dữ liệu để fine-tune.")
    return {"message": "Đã fine-tune cho các câu trả lời.", "documents": len(get_all_documents(db))}

@router.get("/documents", response_model=list[FineTuneDataOut], summary="Danh sách tài liệu huấn luyện")
def list_documents(db: Session = Depends(get_db)):
    """
    Trả về danh sách câu trả lời, và câu trả lời mong muốn đang có.
    """
    docs = get_all_documents(db)
    return docs

@router.delete("/{document_id}", summary="Xóa tài liệu fine-tune theo ID")
def delete_document_endpoint(document_id: int, db: Session = Depends(get_db)):
    """
    Xoá tài liệu fine-tune (FineTuneData) theo ID.
    Lưu ý: Sau khi xóa, có thể cần gọi lại /fine_tune/start để fine-tune lại tài liệu.
    """
    success = delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document không tồn tại.")
    return {"message": f"Đã xoá document với id = {document_id}."}
