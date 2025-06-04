# Chatbot VietNamese Backend

Đây là project backend cho hệ thống Chatbot trả lời tiếng việt, sử dụng [FastAPI](https://fastapi.tiangolo.com/) và [PostgreSQL](https://www.postgresql.org/) làm cơ sở dữ liệu. Project được tổ chức theo mô hình modular, dễ mở rộng và bảo trì.
Chức năng Chatbot là trả lời hội thoại dưới dạng QA. Dữ liệu được nạp dạng danh sách bộ câu hỏi FQA. Chatbot có 2 cơ chế để hiểu bộ dữ liệu là faiss và fine-tune. Và có nhiều endpoint API tương đương phiên bản chat v1, v2,... Các phiên bản chat cũ sẽ được giữ nguyên, các phiên bản chat mới sẽ được tích hợp thêm và mở rộng dưới dạng các endpoint chat trong tương lai.

## Mục lục

- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Chạy ứng dụng](#chạy-ứng-dụng)
- [Môi trường phát triển](#môi-trường-phát-triển)
- [Thông tin liên hệ](#thông-tin-liên-hệ)

---

## Cấu trúc thư mục

```plaintext
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Điểm khởi chạy ứng dụng FastAPI
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── chat.py   # Định nghĩa endpoint /chat
│   │           └── train.py  # Định nghĩa các endpoint /train/...
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Cấu hình biến môi trường (DB URL, khóa bí mật, v.v.)
│   │   └── security.py      # (Tùy chọn) Cấu hình bảo mật như JWT nếu cần
│   ├── models/              # Định nghĩa các ORM model (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py          # Model User (nếu có đăng nhập)
│   │   ├── document.py      # Model Document (câu hỏi-hướng dẫn huấn luyện)
│   │   └── chat_history.py  # Model ChatHistory (lưu lịch sử chat)
│   ├── schemas/             # Định nghĩa Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   └── chat.py
│   ├── services/            # Các business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── document_service.py
│   │   └── chat_service.py
│   ├── db/                  # Cấu hình DB
│   │   ├── __init__.py
│   │   ├── base.py          # Base model (SQLAlchemy declarative base)
│   │   ├── session.py       # Tạo Engine & Session tới PostgreSQL
│   │   └── migrations/      # (Tùy chọn) Alembic migrations
│   └── utils/               # Hàm tiện ích
│       ├── __init__.py
│       └── helpers.py
├── .env                     # Thiết lập biến môi trường (DB URL, etc.)
├── requirements.txt         # Danh sách thư viện Python cần thiết
└── README.md
```

## Yêu cầu hệ thống

- Python 3.8+
- PostgreSQL
- pip

## Cài đặt

1. **Clone repository:**
    ```bash
    git clone https://github.com/thinh22495/chatbot.git backend
    cd backend
    ```

2. **Tạo virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # hoặc venv\Scripts\activate trên Windows
    ```

3. **Cài đặt dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Cấu hình biến môi trường:**
    - Tạo file `.env` dựa trên mẫu dưới đây:
      ```
      DATABASE_URL=postgresql://user:password@localhost:5432/dbname
      SECRET_KEY=your_secret_key
      ```

## Chạy ứng dụng

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs

## Môi trường phát triển

- **Quản lý database:** Sử dụng Alembic cho migration (nếu cần).
- **Testing:** Có thể sử dụng pytest để viết và chạy test.

## Thông tin liên hệ

- Tác giả: Trần Hữu Thịnh
- Email: thinh95.tranhuu@gmail.com

---

> Project này được phát triển với mục đích học tập và nghiên cứu.
