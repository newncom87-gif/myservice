"""쓰기 가능한 데이터 경로(DB, 업로드 배경, 생성된 PPT 출력).

데스크톱 앱은 홈 디렉터리 하위 ~/.bible_ppt_maker 를 그대로 쓰고, Docker(웹
배포)에서는 BIBLE_PPT_DATA_DIR 환경변수로 마운트된 볼륨 경로를 가리키게 한다.
"""
import os
from pathlib import Path


def user_data_dir():
    override = os.environ.get("BIBLE_PPT_DATA_DIR")
    d = Path(override).expanduser() if override else (Path.home() / ".bible_ppt_maker")
    d.mkdir(parents=True, exist_ok=True)
    return d


def uploads_dir():
    d = user_data_dir() / "backgrounds"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path():
    return user_data_dir() / "app.db"


def secret_key_path():
    return user_data_dir() / "secret_key"


def output_dir():
    d = user_data_dir() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d
