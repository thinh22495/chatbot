from fastapi import APIRouter, Depends, Query, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.unknown_question import UnknownQuestion
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import desc
from pydantic import BaseModel
import pandas as pd
from io import BytesIO

from app.schemas.unknown_question import UnknownQuestionOut, UnknownQuestionResponse
from app.models.document import Document

router = APIRouter(prefix="/unknown_question", tags=["Các câu hỏi khác nằm ngoài phạm vi huấn luyện"])

def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Định dạng thời gian MM-DD-YYYY hoặc MM/DD/YYYY"""
    if not date_str:
        return None
        
    try:
        # Try MM-DD-YYYY format
        try:
            return datetime.strptime(date_str, '%m-%d-%Y').date()
        except ValueError:
            # If failed, try MM/DD/YYYY format
            return datetime.strptime(date_str, '%m/%d/%Y').date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Định dạng thời gian không hợp lệ. Hãy sử dụng MM-DD-YYYY hoặc MM/DD/YYYY"
        )

@router.get("/questions", response_model=UnknownQuestionResponse)
def get_unanswered_questions(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Số trang"),
    page_size: int = Query(default=100, ge=1, le=100, description="Số item trên mỗi trang"),
    start_date: Optional[str] = Query(None, description="Ngày bắt đầu (MM-DD-YYYY hoặc MM/DD/YYYY)"),
    end_date: Optional[str] = Query(None, description="Ngày kết thúc (MM-DD-YYYY hoặc MM/DD/YYYY)")
):
    """
    Lấy danh sách câu hỏi chưa có câu trả lời với phân trang và lọc theo ngày
    - **page**: Số trang (bắt đầu từ 1)
    - **page_size**: Số câu hỏi trên mỗi trang
    - **start_date**: Lọc từ ngày (MM-DD-YYYY hoặc MM/DD/YYYY)
    - **end_date**: Lọc đến ngày (MM-DD-YYYY hoặc MM/DD/YYYY)
    """
    query = db.query(UnknownQuestion)
    
    # Parse và áp dụng bộ lọc ngày
    parsed_start_date = parse_date(start_date)
    parsed_end_date = parse_date(end_date)
    
    if parsed_start_date:
        query = query.filter(UnknownQuestion.timestamp >= datetime.combine(parsed_start_date, datetime.min.time()))
    if parsed_end_date:
        query = query.filter(UnknownQuestion.timestamp <= datetime.combine(parsed_end_date, datetime.max.time()))
    
    # Tính tổng số records để phân trang
    total_records = query.count()
    
    # Áp dụng phân trang và sắp xếp
    questions = (query
                .order_by(desc(UnknownQuestion.timestamp))
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all())
    
    # Tính toán thông tin phân trang
    total_pages = (total_records + page_size - 1) // page_size
    
    return {
        "items": questions,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": total_pages
        }
    }

@router.delete("/clear-all")
def delete_all_questions(
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
        count = db.query(UnknownQuestion).delete()
        db.commit()
        
        return {
            "status": "success",
            "message": f"Đã xóa {count} câu hỏi",
            "deleted_count": count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xóa dữ liệu: {str(e)}"
        )

@router.get("/export-excel")
def export_to_excel(
    db: Session = Depends(get_db),
):
    """
    Export toàn bộ danh sách câu hỏi ra file Excel.
    """
    try:
        # Lấy toàn bộ dữ liệu và sắp xếp theo thời gian mới nhất
        questions = db.query(UnknownQuestion).order_by(desc(UnknownQuestion.timestamp)).all()
        
        if not questions:
            raise HTTPException(
                status_code=404,
                detail="Không có dữ liệu để export"
            )

        # Chuyển đổi dữ liệu sang DataFrame
        data = [{
            "ID": q.id,
            "Câu hỏi": q.question,
            "Thời gian": q.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for q in questions]
        
        df = pd.DataFrame(data)
        
        # Tạo và định dạng file Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Câu hỏi chưa trả lời')
            
            # Tự động điều chỉnh độ rộng cột
            worksheet = writer.sheets['Câu hỏi chưa trả lời']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        buffer.seek(0)
        
        # Tạo tên file với timestamp
        filename = f"unknown_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
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
