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
│   └── utils/               # Hàm tiện ích (ví dụ xử lý file, embeddings,...)
│       ├── __init__.py
│       └── helpers.py
├── .env                     # Thiết lập biến môi trường (DB URL, etc.)
├── requirements.txt         # Danh sách thư viện Python cần thiết
└── README.md
