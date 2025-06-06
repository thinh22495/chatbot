# Chatbot Backend (VietNamese)

Đây là backend cho hệ thống Chatbot trả lời tiếng Việt, xây dựng bằng [FastAPI](https://fastapi.tiangolo.com/) và sử dụng [PostgreSQL](https://www.postgresql.org/) làm cơ sở dữ liệu.  
Project hỗ trợ các chức năng quản lý tài liệu huấn luyện (FAQ), upload dữ liệu, xây dựng và cập nhật chỉ mục tìm kiếm (FAISS), cũng như các endpoint API phục vụ hội thoại chatbot.

**Các tính năng chính:**
- Quản lý tài liệu huấn luyện (thêm, xóa, xuất dữ liệu, phân trang)
- Upload file Excel để bổ sung dữ liệu huấn luyện
- Xây dựng và cập nhật FAISS index để tìm kiếm câu trả lời nhanh chóng
- Hỗ trợ nhiều phiên bản endpoint chat (v1, v2, ...)
- Dễ dàng mở rộng, tích hợp thêm các mô hình hoặc chức năng mới
- Sử dụng Alembic để quản lý migration cho database
- Đóng gói và triển khai thuận tiện với Docker/Docker Compose

Project phù hợp cho các bài toán chatbot FAQ, tư vấn tự động, hoặc làm nền tảng phát triển các hệ thống hỏi đáp tiếng Việt.

## Mục lục

- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Chạy ứng dụng trực tiếp](#chạy-ứng-dụng-trực-tiếp)
- [Chạy ứng dụng bằng Docker](#chạy-ứng-dụng-bằng-docker)
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

## Chạy ứng dụng trực tiếp

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs

## Chạy ứng dụng bằng Docker

1. **Cài đặt Docker và Docker Compose**  
   Đảm bảo bạn đã cài [Docker](https://www.docker.com/products/docker-desktop/) và [Docker Compose](https://docs.docker.com/compose/).

2. **Cấu hình biến môi trường**  
   Tạo file `.env` ở thư mục gốc (nếu chưa có), ví dụ:
   ```
   POSTGRES_USER=chatbot
   POSTGRES_PASSWORD=chatbot
   POSTGRES_SERVER=db
   POSTGRES_DB=chatbotdb
   POSTGRES_PORT=5432
   ```

3. **Chạy ứng dụng với Docker Compose**  
   ```bash
   docker-compose up --build
   ```

   - Lần đầu chạy sẽ tự động build image và khởi tạo database.
   - API docs: http://localhost:8000/docs

4. **Chạy migration (nếu cần thủ công):**  
   Nếu muốn chạy migration thủ công, vào container backend:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

---

**Lưu ý:**  
- Nếu thay đổi models, hãy tạo migration mới rồi chạy lại migration trong container backend.
- Dữ liệu PostgreSQL sẽ được lưu trong volume `postgres_data` (không mất khi dừng container).

---

## Môi trường phát triển

- **Quản lý database:** Sử dụng Alembic cho migration (nếu cần).
- **Testing:** Có thể sử dụng pytest để viết và chạy test.

## Thông tin liên hệ

- Tác giả: Trần Hữu Thịnh
- Email: thinh95.tranhuu@gmail.com

---

> Project này được phát triển với mục đích học tập và nghiên cứu.
