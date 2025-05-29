# app/api/v1/endpoints/train.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Header
from sqlalchemy.orm import Session
import pandas as pd
from fastapi.responses import FileResponse
from io import BytesIO
from datetime import datetime

from app.schemas.document import DocumentOut
from app.models.document import Document
from app.schemas.common import PaginationResponse
from app.services.document_service import create_documents_from_excel, delete_document, get_all_documents
from app.services.chat_service import rebuild_faiss_index
from app.db.session import SessionLocal, get_db

router = APIRouter(prefix="/train", tags=["train"])

# First, create a pagination response schema if not exists
class DocumentResponse(PaginationResponse):
    items: list[DocumentOut]

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

@router.get("/documents", response_model=DocumentResponse, summary="Danh sách tài liệu huấn luyện (có phân trang)")
def list_documents(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Số trang"),
    page_size: int = Query(default=10, ge=1, le=100, description="Số item trên mỗi trang")
):
    """
    Trả về danh sách các tài liệu (câu hỏi và hướng dẫn) đang có, có phân trang.
    
    Parameters:
    - page: Số trang (bắt đầu từ 1)
    - page_size: Số lượng item trên mỗi trang (1-100)
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total_records = db.query(Document).count()
    
    # Get paginated documents
    docs = (db.query(Document)
            .order_by(Document.id)
            .offset(offset)
            .limit(page_size)
            .all())
    
    # Calculate total pages
    total_pages = (total_records + page_size - 1) // page_size
    
    return {
        "items": docs,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": total_pages
        }
    }

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

@router.get("/export-excel", summary="Xuất toàn bộ tài liệu huấn luyện ra Excel")
def export_documents_to_excel(
    db: Session = Depends(get_db),
):
    """
    Export toàn bộ danh sách tài liệu huấn luyện ra file Excel.
    """
    try:
        # Lấy toàn bộ documents
        documents = db.query(Document).order_by(Document.id).all()
        
        if not documents:
            raise HTTPException(
                status_code=404,
                detail="Không có dữ liệu để export"
            )

        # Chuyển đổi thành DataFrame
        data = [{
            "ID": doc.id,
            "Câu hỏi": doc.question,
            "Câu trả lời": doc.answer
        } for doc in documents]
        
        df = pd.DataFrame(data)
        
        # Tạo buffer cho file Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Tài liệu huấn luyện')
            
            # Tự động điều chỉnh độ rộng cột
            worksheet = writer.sheets['Tài liệu huấn luyện']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                # Add a little extra width to the column
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        buffer.seek(0)
        
        # Tạo tên file với timestamp
        filename = f"training_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return FileResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi export dữ liệu: {str(e)}"
        )

@router.delete("/clear-all")
def delete_all_documents(
    db: Session = Depends(get_db),
    confirm: bool = Query(False, description="Xác nhận xóa toàn bộ dữ liệu"),
    x_admin_token: str = Header(None, description="Admin token for authentication")
):
    """
    Xóa toàn bộ câu hỏi trong bảng UnknownQuestion.
    Yêu cầu xác nhận và admin token.
    
    - **confirm**: Phải set true để xác nhận xóa
    - **x_admin_token**: Token xác thực admin
    """
    # Kiểm tra admin token
    if x_admin_token != "your-admin-token":  # Thay thế bằng logic xác thực thực tế
        raise HTTPException(
            status_code=403,
            detail="Không có quyền thực hiện thao tác này"
        )
    
    # Yêu cầu xác nhận
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Vui lòng xác nhận xóa bằng cách set confirm=true"
        )
    
    try:
        # Xóa toàn bộ records
        count = db.query(Document).delete()
        db.commit()
        
        return {
            "status": "success",
            "message": f"Đã xóa {count} dữ liệu.",
            "deleted_count": count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xóa dữ liệu: {str(e)}"
        )