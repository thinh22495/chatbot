# app/services/fine_tune_data_service.py
from sqlalchemy.orm import Session
from app.models.fine_tune_data import FineTuneData

def create_documents_from_excel(df, db: Session):
    """
    Tạo nhiều bản ghi Document từ DataFrame đọc được từ Excel.
    Cột đầu là answer, cột thứ hai là target (mong muốn theo các ngữ cảnh).
    """
    docs = []
    for index, row in df.iterrows():
        answer = str(row[0]).strip()
        target = str(row[1]).strip()
        if answer and target:
            doc = FineTuneData(answer=answer, target=target)
            db.add(doc)
            docs.append(doc)
    db.commit()
    return docs

def delete_document(doc_id: int, db: Session):
    doc = db.query(FineTuneData).get(doc_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True

def get_all_documents(db: Session):
    return db.query(FineTuneData).all()
