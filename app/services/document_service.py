# app/services/document_service.py
from sqlalchemy.orm import Session
from app.models.document import Document

def create_documents_from_excel(df, db: Session):
    """
    Tạo nhiều bản ghi Document từ DataFrame đọc được từ Excel.
    Cột đầu là question, cột thứ hai là answer.
    """
    docs = []
    for index, row in df.iterrows():
        question = str(row[0]).strip()
        answer = str(row[1]).strip()
        if question and answer:
            doc = Document(question=question, answer=answer)
            db.add(doc)
            docs.append(doc)
    db.commit()
    return docs

def delete_document(doc_id: int, db: Session):
    doc = db.query(Document).get(doc_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True

def get_all_documents(db: Session):
    return db.query(Document).all()
