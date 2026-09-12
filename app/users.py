"""계정 관리 (관리자가 scripts/manage_users.py로 생성/삭제)."""
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


def create_user(username, password):
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_by_id(user_id):
    conn = db.get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def get_by_username(username):
    conn = db.get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()


def verify_password(username, password):
    row = get_by_username(username)
    if not row or not check_password_hash(row["password_hash"], password):
        return None
    return row


def set_password(username, new_password):
    conn = db.get_connection()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (generate_password_hash(new_password), username),
        )
        conn.commit()
    finally:
        conn.close()


def list_users():
    conn = db.get_connection()
    try:
        return conn.execute("SELECT id, username, created_at FROM users ORDER BY username").fetchall()
    finally:
        conn.close()


def delete_user(username):
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
    finally:
        conn.close()
