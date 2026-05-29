"""Servicios de autenticación y gestión de usuarios locales."""

import hashlib
import secrets
import sqlite3
from typing import Any, Dict

from app.services.session_store import _connect, _now, init_db


def init_users_table():
    """Crea la tabla de usuarios y garantiza el usuario admin por defecto."""
    init_db()

    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt          TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
            """
        )
        conn.commit()
        _create_default_admin(conn)


def _create_default_admin(conn):
    """Crea el usuario admin por defecto si no existe."""
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?", ("admin",)
    ).fetchone()

    if not existing:
        salt, password_hash = _hash_password("admin")
        conn.execute(
            """
            INSERT INTO users (username, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ("admin", password_hash, salt, _now()),
        )
        conn.commit()


def _hash_password(password: str, salt: str = None):
    """Calcula `salt` y hash SHA-256 para registro o validación de login."""
    if salt is None:
        salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, password_hash


def register_user(username: str, password: str) -> Dict[str, Any]:
    """Registra un nuevo usuario y devuelve resultado estructurado."""
    init_users_table()

    username = username.strip()
    password = password.strip()

    if not username or not password:
        return {"ok": False, "error": "Los campos no pueden estar vacíos."}

    if len(password) < 6:
        return {"ok": False, "error": "La contraseña debe tener al menos 6 caracteres."}

    if len(username) < 3:
        return {"ok": False, "error": "El usuario debe tener al menos 3 caracteres."}

    salt, password_hash = _hash_password(password)

    try:
        with _connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (username, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, password_hash, salt, _now()),
            )
            conn.commit()

            user_id = cursor.lastrowid

        return {"ok": True, "id": user_id, "username": username}

    except sqlite3.IntegrityError:
        return {"ok": False, "error": "El nombre de usuario ya está en uso."}

    except Exception as e:
        return {"ok": False, "error": f"Error interno: {str(e)}"}


def login_user(username: str, password: str) -> Dict[str, Any]:
    """Verifica credenciales de usuario y devuelve resultado estructurado."""
    init_users_table()

    username = username.strip()
    password = password.strip()

    if not username or not password:
        return {"ok": False, "error": "Los campos no pueden estar vacíos."}

    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if not row:
        return {"ok": False, "error": "Credenciales incorrectas."}

    _, password_hash = _hash_password(password, salt=row["salt"])

    if password_hash != row["password_hash"]:
        return {"ok": False, "error": "Credenciales incorrectas."}

    return {"ok": True, "id": row["id"], "username": row["username"]}
