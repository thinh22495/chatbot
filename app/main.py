# app/main.py
from fastapi import FastAPI
from app.api.v1.endpoints import chat, train, fine_tune, unknown_question
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Chatbot AI")

app.include_router(chat.router)
app.include_router(train.router)
app.include_router(fine_tune.router)
app.include_router(unknown_question.router)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins, trong môi trường thực tế nên giới hạn cụ thể
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả methods
    allow_headers=["*"],  # Cho phép tất cả headers
)