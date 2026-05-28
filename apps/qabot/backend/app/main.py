from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import router as chat_router
from app.routes.ci import router as ci_router
from app.routes.auth import router as auth_router
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
app.include_router(ci_router)
app.include_router(auth_router)
