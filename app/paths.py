"""사용자별 쓰기 가능한 데이터 경로(업로드 배경, 테마, 생성된 PPT 출력)."""
from pathlib import Path


def user_data_dir():
    d = Path.home() / ".bible_ppt_maker"
    d.mkdir(parents=True, exist_ok=True)
    return d


def uploads_dir():
    d = user_data_dir() / "backgrounds"
    d.mkdir(parents=True, exist_ok=True)
    return d


def themes_path():
    return user_data_dir() / "themes.json"


def projects_path():
    return user_data_dir() / "projects.json"


def output_dir():
    d = user_data_dir() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d
