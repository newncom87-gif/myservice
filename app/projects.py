"""작업(구절 블록+분배+배경+테마 전체 상태) 저장·불러오기 (사용자별로 분리, SQLite).

"테마"(themes.py)는 표지/본문 서식만 저장하는 반면, "작업"은 그 서식을 포함해
어떤 구절을 선택했는지, 슬라이드를 어떻게 나눴는지, 배경은 무엇을 골랐는지까지
통째로 저장해서 나중에 이어서 작업할 수 있게 한다.
"""
import json

from . import db


def load_projects(user_id):
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT data FROM projects WHERE user_id = ? ORDER BY name", (user_id,)
        ).fetchall()
        return [json.loads(r["data"]) for r in rows]
    finally:
        conn.close()


def save_project(user_id, project):
    if not project.get("name"):
        raise ValueError("작업 이름이 필요합니다")
    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO projects (user_id, name, data, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, name) DO UPDATE SET
                data = excluded.data, updated_at = excluded.updated_at
            """,
            (user_id, project["name"], json.dumps(project, ensure_ascii=False)),
        )
        conn.commit()
    finally:
        conn.close()
    return load_projects(user_id)


def delete_project(user_id, name):
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM projects WHERE user_id = ? AND name = ?", (user_id, name))
        conn.commit()
    finally:
        conn.close()
    return load_projects(user_id)
