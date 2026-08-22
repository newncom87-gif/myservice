"""표지/본문 서식 테마 저장·불러오기 (사용자 데이터 폴더의 themes.json)."""
import json

from . import paths


def load_themes():
    p = paths.themes_path()
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def save_theme(theme):
    if not theme.get("name"):
        raise ValueError("테마 이름이 필요합니다")
    themes = [t for t in load_themes() if t["name"] != theme["name"]]
    themes.append(theme)
    with paths.themes_path().open("w", encoding="utf-8") as f:
        json.dump(themes, f, ensure_ascii=False, indent=2)
    return themes


def delete_theme(name):
    themes = [t for t in load_themes() if t["name"] != name]
    with paths.themes_path().open("w", encoding="utf-8") as f:
        json.dump(themes, f, ensure_ascii=False, indent=2)
    return themes
