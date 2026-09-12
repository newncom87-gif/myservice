"""표지/본문 서식 테마 저장·불러오기 (사용자별로 분리, SQLite)."""
import json

from . import db


def load_themes(user_id):
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT data FROM themes WHERE user_id = ? ORDER BY name", (user_id,)
        ).fetchall()
        return [json.loads(r["data"]) for r in rows]
    finally:
        conn.close()


def save_theme(user_id, theme):
    if not theme.get("name"):
        raise ValueError("테마 이름이 필요합니다")
    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO themes (user_id, name, data, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, name) DO UPDATE SET
                data = excluded.data, updated_at = excluded.updated_at
            """,
            (user_id, theme["name"], json.dumps(theme, ensure_ascii=False)),
        )
        conn.commit()
    finally:
        conn.close()
    return load_themes(user_id)


def delete_theme(user_id, name):
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM themes WHERE user_id = ? AND name = ?", (user_id, name))
        conn.commit()
    finally:
        conn.close()
    return load_themes(user_id)
