from fastapi import APIRouter
from pydantic import BaseModel
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class AuthRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: AuthRequest):
    result = login_user(data.username, data.password)
    if not result["ok"]:
        return {"ok": False, "error": result["error"]}

    user_id = result.get("id")
    return {"ok": True, "id": str(user_id), "username": result["username"]}


@router.post("/register")
def register(data: AuthRequest):
    result = register_user(data.username, data.password)
    if not result["ok"]:
        return {"ok": False, "error": result["error"]}

    user_id = result.get("id")
    return {"ok": True, "id": str(user_id), "username": result["username"]}
