"""Router alternativo de autenticación de QABot."""

from app.services.auth_service import login_user, register_user
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AuthRequest(BaseModel):
    """Payload de entrada para autenticación de usuario."""

    username: str
    password: str


@router.post("/login")
def login(data: AuthRequest):
    """Inicia sesión con usuario y contraseña."""
    result = login_user(data.username, data.password)
    if not result["ok"]:
        return {"ok": False, "error": result["error"]}
    user_id = result.get("id")
    return {"ok": True, "id": str(user_id), "username": result["username"]}


@router.post("/register")
def register(data: AuthRequest):
    """Registra un nuevo usuario en el sistema."""
    result = register_user(data.username, data.password)
    if not result["ok"]:
        return {"ok": False, "error": result["error"]}
    user_id = result.get("id")
    return {"ok": True, "id": str(user_id), "username": result["username"]}
