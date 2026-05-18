from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.chat_router import router as chat_router
from app.routers.auth_router import router as auth_router
from app.services.session_store import init_db
from app.services.auth_service import init_users_table

app = FastAPI()
init_db()
init_users_table()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(auth_router, prefix="/auth")