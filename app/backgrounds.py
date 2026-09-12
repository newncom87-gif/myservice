"""기본/사용자 배경이미지 목록 및 경로 해석."""
import json
from pathlib import Path

from . import paths

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DIR = APP_DIR / "static" / "backgrounds" / "default"
MANIFEST_PATH = APP_DIR / "data" / "backgrounds_default.json"

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def list_default():
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def list_user():
    items = []
    for p in sorted(paths.uploads_dir().glob("*")):
        if p.suffix.lower() in ALLOWED_EXT:
            items.append({"id": p.name, "name": p.stem, "file": p.name})
    return items


def resolve_path(ref):
    """ref: {"defaultId": id} 또는 {"uploadId": filename} -> 실제 파일 Path"""
    if not ref:
        return None
    if ref.get("defaultId"):
        manifest = {b["id"]: b for b in list_default()}
        item = manifest.get(ref["defaultId"])
        if not item:
            raise ValueError(f"알 수 없는 기본 배경: {ref['defaultId']}")
        return DEFAULT_DIR / item["file"]
    if ref.get("uploadId"):
        p = paths.uploads_dir() / Path(ref["uploadId"]).name
        if not p.exists():
            raise ValueError(f"업로드 배경을 찾을 수 없습니다: {ref['uploadId']}")
        return p
    raise ValueError("배경 참조가 올바르지 않습니다")
