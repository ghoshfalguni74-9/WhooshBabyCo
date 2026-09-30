import sqlite3
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "login_database.db"


def ensure_admin_data_dir(base_dir: Path | None = None) -> Path:
    """Create the admin data directory if it does not exist."""
    admin_dir = (base_dir or Path(__file__).resolve().parent / "data").resolve()
    admin_dir.mkdir(parents=True, exist_ok=True)
    return admin_dir


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Return a SQLite connection to the login database."""
    target = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    return connection


def create_login_table(db_path: str | Path | None = None) -> Path:
    """Create the table used to store legacy login records."""
    target = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(target) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    return target


def create_users_table(db_path: str | Path | None = None) -> Path:
    """Create the table used for full user registration data."""
    target = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(target) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                building TEXT,
                locality TEXT,
                city TEXT,
                district TEXT,
                country TEXT,
                pincode TEXT,
                landmark TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    return target


def save_login(username: str, password: str, db_path: str | Path | None = None) -> None:
    """Save a username/password pair into the database."""
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO login_records (username, password) VALUES (?, ?)",
            (username, password),
        )


def list_logins(db_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Return all stored login records."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, username, password, created_at FROM login_records ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def user_exists(email: str, db_path: str | Path | None = None) -> bool:
    """Check whether an email already exists in the user table."""
    create_users_table(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1",
            (email,),
        ).fetchone()
        return row is not None


def create_user_account(data: Dict[str, Any], db_path: str | Path | None = None) -> Dict[str, Any]:
    """Insert a full user signup payload into the database."""
    create_users_table(db_path)
    email = (data.get("email") or "").strip()
    if not email:
        raise ValueError("Email is required")

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (
                name, dob, gender, email, phone, building, locality, city, district, country,
                pincode, landmark, password
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (data.get("name") or "").strip(),
                (data.get("dob") or "").strip(),
                (data.get("gender") or "").strip(),
                email,
                (data.get("phone") or "").strip(),
                (data.get("building") or "").strip(),
                (data.get("locality") or "").strip(),
                (data.get("city") or "").strip(),
                (data.get("district") or "").strip(),
                (data.get("country") or "").strip(),
                (data.get("pincode") or "").strip(),
                (data.get("landmark") or "").strip(),
                data.get("password") or "",
            ),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "email": email}


def verify_login(email: str, password: str, db_path: str | Path | None = None) -> bool:
    """Verify whether email/password matches an existing user."""
    create_users_table(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE LOWER(email) = LOWER(?) AND password = ? LIMIT 1",
            (email, password),
        ).fetchone()
        return row is not None


def update_user_password(email: str, password: str, db_path: str | Path | None = None) -> bool:
    """Update the password for an existing user."""
    create_users_table(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "UPDATE users SET password = ? WHERE LOWER(email) = LOWER(?)",
            (password, email),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_user_details(email: str, data: Dict[str, Any], db_path: str | Path | None = None) -> bool:
    """Update editable profile fields for an existing user."""
    create_users_table(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE users SET
                name = ?, dob = ?, gender = ?, phone = ?, building = ?, locality = ?,
                city = ?, district = ?, country = ?, pincode = ?, landmark = ?
            WHERE LOWER(email) = LOWER(?)
            """,
            (
                (data.get("name") or "").strip(),
                (data.get("dob") or "").strip(),
                (data.get("gender") or "").strip(),
                (data.get("phone") or "").strip(),
                (data.get("building") or "").strip(),
                (data.get("locality") or "").strip(),
                (data.get("city") or "").strip(),
                (data.get("district") or "").strip(),
                (data.get("country") or "").strip(),
                (data.get("pincode") or "").strip(),
                (data.get("landmark") or "").strip(),
                email,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_user_by_email(email: str, db_path: str | Path | None = None) -> Dict[str, Any] | None:
    """Fetch a user record by email."""
    create_users_table(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT name, dob, gender, email, phone, building AS building_no, locality, city, district,
                   country, pincode, landmark, password
            FROM users WHERE LOWER(email) = LOWER(?)
            LIMIT 1
            """,
            (email,),
        ).fetchone()
        return dict(row) if row is not None else None
