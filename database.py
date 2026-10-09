
import sqlite3
import hashlib
import hmac

DB_NAME = "fraud_detection.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def signup(full_name, email, password):
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name or not email or not password:
        return False, "Please fill in all fields."

    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (full_name, email, hash_password(password))
            )
        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "This email is already registered."


def login(email, password):
    email = email.strip().lower()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, full_name, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    if row and hmac.compare_digest(
        row[3], hash_password(password)
    ):
        return {
            "id": row[0],
            "full_name": row[1],
            "email": row[2]
        }

    return None


def get_user(user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, full_name, email FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

    if row:
        return {
            "id": row[0],
            "full_name": row[1],
            "email": row[2]
        }

    return None


init_db()
