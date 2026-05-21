import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "qabot_state.db"


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,

                project_label TEXT,
                test_phase TEXT,
                review_label TEXT,

                active_review_prompt TEXT,
                pending_prompt TEXT,
                last_processed_file_name TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # Defensive migration from the previous monouser/demo schema.
        session_columns = _table_columns(conn, "sessions")
        if "user_id" not in session_columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                execution_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS phase_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                prompt TEXT,
                detected_phase TEXT,
                comment TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
            """
        )

        conn.commit()


def _require_user_id(user_id: Optional[str]) -> str:
    clean = str(user_id or "").strip()
    if not clean:
        raise ValueError("user_id es obligatorio para operaciones de sesión autenticadas.")
    return clean


def create_session(
    project_label: Optional[str] = None,
    test_phase: Optional[str] = None,
    review_label: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    init_db()
    clean_user_id = _require_user_id(user_id)

    session_id = f"CQA-{uuid.uuid4().hex[:8].upper()}"
    now = _now()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (
                session_id,
                user_id,
                project_label,
                test_phase,
                review_label,
                active_review_prompt,
                pending_prompt,
                last_processed_file_name,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
            """,
            (
                session_id,
                clean_user_id,
                _clean_optional(project_label),
                _clean_optional(test_phase),
                _clean_optional(review_label),
                now,
                now,
            ),
        )
        conn.commit()

    return get_session(session_id, clean_user_id)


def get_session(session_id: str, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    init_db()
    clean_user_id = _require_user_id(user_id)

    with _connect() as conn:
        session = conn.execute(
            """
            SELECT *
            FROM sessions
            WHERE session_id = ? AND user_id = ?
            """,
            (session_id, clean_user_id),
        ).fetchone()

        if not session:
            return None

        messages = conn.execute(
            """
            SELECT role, content, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

        reports = conn.execute(
            """
            SELECT execution_id, report_json, created_at
            FROM reports
            WHERE session_id = ?
            ORDER BY created_at DESC
            """,
            (session_id,),
        ).fetchall()

    parsed_reports = _parse_reports(reports)

    return {
        "session_id": session["session_id"],
        "user_id": session["user_id"],

        "project_label": session["project_label"],
        "test_phase": session["test_phase"],
        "review_label": session["review_label"],

        "active_review_prompt": session["active_review_prompt"],
        "pending_prompt": session["pending_prompt"],
        "last_processed_file_name": session["last_processed_file_name"],

        "created_at": session["created_at"],
        "updated_at": session["updated_at"],

        "messages": [dict(row) for row in messages],
        "reports": parsed_reports,
        "last_report": parsed_reports[0] if parsed_reports else None,
    }


def list_sessions(user_id: Optional[str]) -> List[Dict[str, Any]]:
    init_db()
    clean_user_id = _require_user_id(user_id)

    with _connect() as conn:
        sessions = conn.execute(
            """
            SELECT *
            FROM sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (clean_user_id,),
        ).fetchall()

        rows = []

        for session in sessions:
            reports = conn.execute(
                """
                SELECT execution_id, report_json, created_at
                FROM reports
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session["session_id"],),
            ).fetchall()

            parsed_reports = _parse_reports(reports)
            last_report = parsed_reports[-1] if parsed_reports else None

            rows.append(
                {
                    "session_id": session["session_id"],
                    "user_id": session["user_id"],

                    "project_label": session["project_label"],
                    "test_phase": session["test_phase"],
                    "review_label": session["review_label"],

                    "active_review_prompt": session["active_review_prompt"],
                    "pending_prompt": session["pending_prompt"],
                    "last_processed_file_name": session["last_processed_file_name"],

                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],

                    "iteration_count": len(parsed_reports),
                    "last_status": (
                        last_report.get("global_status") if last_report else None
                    ),
                    "last_execution_id": (
                        last_report.get("execution_id") if last_report else None
                    ),
                    "title": session["review_label"] or _build_session_title(session, parsed_reports),
                }
            )

        return rows


def update_session_state(
    session_id: str,
    user_id: Optional[str],
    active_review_prompt: Optional[str] = None,
    pending_prompt: Optional[str] = None,
    last_processed_file_name: Optional[str] = None,
):
    init_db()
    clean_user_id = _require_user_id(user_id)

    with _connect() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET active_review_prompt = ?,
                pending_prompt = ?,
                last_processed_file_name = ?,
                updated_at = ?
            WHERE session_id = ? AND user_id = ?
            """,
            (
                active_review_prompt,
                pending_prompt,
                last_processed_file_name,
                _now(),
                session_id,
                clean_user_id,
            ),
        )
        conn.commit()


def update_session_metadata(
    session_id: str,
    user_id: Optional[str],
    project_label: Optional[str] = None,
    test_phase: Optional[str] = None,
    review_label: Optional[str] = None,
):
    init_db()
    clean_user_id = _require_user_id(user_id)

    with _connect() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET project_label = ?,
                test_phase = ?,
                review_label = ?,
                updated_at = ?
            WHERE session_id = ? AND user_id = ?
            """,
            (
                _clean_optional(project_label),
                _clean_optional(test_phase),
                _clean_optional(review_label),
                _now(),
                session_id,
                clean_user_id,
            ),
        )
        conn.commit()


def add_message(
    session_id: str,
    role: str,
    content: str,
    timestamp: Optional[str] = None,
):
    init_db()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, role, content, timestamp, _now()),
        )
        conn.execute(
            """
            UPDATE sessions
            SET updated_at = ?
            WHERE session_id = ?
            """,
            (_now(), session_id),
        )
        conn.commit()


def add_report(session_id: str, report: Dict[str, Any]):
    init_db()

    execution_id = report.get("execution_id")

    if not execution_id:
        return

    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO reports (execution_id, session_id, report_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                execution_id,
                session_id,
                json.dumps(report, ensure_ascii=False),
                _now(),
            ),
        )
        conn.execute(
            """
            UPDATE sessions
            SET updated_at = ?
            WHERE session_id = ?
            """,
            (_now(), session_id),
        )
        conn.commit()


def get_report(execution_id: str, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    init_db()
    clean_user_id = _require_user_id(user_id)

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT reports.report_json
            FROM reports
            INNER JOIN sessions ON sessions.session_id = reports.session_id
            WHERE reports.execution_id = ? AND sessions.user_id = ?
            """,
            (execution_id, clean_user_id),
        ).fetchone()

    if not row:
        return None

    return json.loads(row["report_json"])


def clear_session(session_id: str, user_id: Optional[str]) -> bool:
    init_db()
    clean_user_id = _require_user_id(user_id)

    with _connect() as conn:
        valid = conn.execute(
            """
            SELECT session_id
            FROM sessions
            WHERE session_id = ? AND user_id = ?
            """,
            (session_id, clean_user_id),
        ).fetchone()

        if not valid:
            return False

        conn.execute("DELETE FROM reports WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

    return True


def _parse_reports(report_rows) -> List[Dict[str, Any]]:
    parsed_reports = []

    for row in report_rows:
        try:
            parsed_reports.append(json.loads(row["report_json"]))
        except Exception:
            continue

    return parsed_reports


def _build_session_title(session, reports: List[Dict[str, Any]]) -> str:
    prompt = session["active_review_prompt"] or session["pending_prompt"]

    if prompt:
        cleaned = " ".join(prompt.split())
        if len(cleaned) > 60:
            return cleaned[:57] + "..."
        return cleaned

    if reports:
        activity = reports[-1].get("activity_type", "Ciclo QA")
        return f"Ciclo {activity}"

    return f"Ciclo {session['session_id']}"


def _clean_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned if cleaned else None


def add_phase_feedback(
    session_id: str,
    prompt: Optional[str] = None,
    detected_phase: Optional[str] = None,
    comment: Optional[str] = None,
):
    init_db()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO phase_feedback (
                session_id,
                prompt,
                detected_phase,
                comment,
                created_at,
                status
            )
            VALUES (?, ?, ?, ?, ?, 'OPEN')
            """,
            (
                session_id,
                prompt,
                detected_phase,
                comment,
                _now(),
            ),
        )
        conn.commit()
