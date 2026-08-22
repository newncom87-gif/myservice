"""작업(구절 블록+분배+배경+테마 전체 상태) 저장·불러오기.

"테마"(themes.py)는 표지/본문 서식만 저장하는 반면, "작업"은 그 서식을 포함해
어떤 구절을 선택했는지, 슬라이드를 어떻게 나눴는지, 배경은 무엇을 골랐는지까지
통째로 저장해서 나중에 이어서 작업할 수 있게 한다.
"""
import json

from . import paths


def load_projects():
    p = paths.projects_path()
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def save_project(project):
    if not project.get("name"):
        raise ValueError("작업 이름이 필요합니다")
    projects = [x for x in load_projects() if x["name"] != project["name"]]
    projects.append(project)
    with paths.projects_path().open("w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)
    return projects


def delete_project(name):
    projects = [x for x in load_projects() if x["name"] != name]
    with paths.projects_path().open("w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)
    return projects
