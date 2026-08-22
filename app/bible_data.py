"""bible.json 을 로드하고 책/장/절 조회, 범위 텍스트 추출을 제공한다."""
import json
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "bible.json"


@lru_cache(maxsize=1)
def _load():
    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _book_map():
    return {b["abbr"]: b for b in _load()["books"]}


def get_books():
    """정경 순서로 정렬된 책 목록: [{abbr, name, order}, ...]"""
    return _load()["books"]


def get_book(abbr):
    b = _book_map().get(abbr)
    if not b:
        raise ValueError(f"알 수 없는 책 약어: {abbr}")
    return b


def get_chapters(abbr):
    """해당 책의 장 번호 목록(오름차순 정수)."""
    chapters = _load()["verses"].get(abbr, {})
    return sorted(int(c) for c in chapters.keys())


def get_verse_units(abbr, chapter):
    """해당 책/장의 절 유닛 목록(절 번호 오름차순). 각 유닛: {v, vEnd, subtitle, text}"""
    units = _load()["verses"].get(abbr, {}).get(str(chapter), [])
    return sorted(units, key=lambda u: u["v"])


def get_max_verse(abbr, chapter):
    units = get_verse_units(abbr, chapter)
    if not units:
        raise ValueError(f"{abbr}{chapter}장이 존재하지 않습니다")
    return max(u["vEnd"] for u in units)


def resolve_range(abbr, start_chapter, start_verse, end_chapter, end_verse):
    """책 하나 안에서 (시작장:시작절) ~ (끝장:끝절) 범위의 절 유닛들을 순서대로 반환.

    반환 항목: {book: abbr, bookName, chapter, v, vEnd, subtitle, text}
    """
    if (end_chapter, end_verse) < (start_chapter, start_verse):
        raise ValueError("끝 위치가 시작 위치보다 앞설 수 없습니다")

    book = get_book(abbr)
    result = []
    for chapter in get_chapters(abbr):
        if chapter < start_chapter or chapter > end_chapter:
            continue
        for u in get_verse_units(abbr, chapter):
            if chapter == start_chapter and u["vEnd"] < start_verse:
                continue
            if chapter == end_chapter and u["v"] > end_verse:
                continue
            result.append({
                "book": abbr,
                "bookName": book["name"],
                "chapter": chapter,
                "v": u["v"],
                "vEnd": u["vEnd"],
                "subtitle": u["subtitle"],
                "text": u["text"],
            })
    return result


def format_ref(book_name, chapter, v, vEnd=None, end_chapter=None, end_v=None):
    """구절 참조 문자열 포맷. 단일 유닛(vEnd) 또는 블록 범위(end_chapter/end_v) 모두 지원."""
    if end_chapter is not None:
        if end_chapter == chapter:
            if end_v == v:
                return f"{book_name} {chapter}:{v}"
            return f"{book_name} {chapter}:{v}~{end_v}"
        return f"{book_name} {chapter}:{v}~{end_chapter}:{end_v}"
    if vEnd and vEnd != v:
        return f"{book_name} {chapter}:{v}~{vEnd}"
    return f"{book_name} {chapter}:{v}"


def format_slide_ref(verses):
    """한 슬라이드에 담긴 절 목록을 표제용 참조 문자열로 요약한다.

    같은 책/장 안의 절이면 "마가복음 6:30~32"처럼 하나로 묶고, 책이나 장이
    섞여 있으면 절별 참조를 쉼표로 나열한다.
    """
    if not verses:
        return ""
    books_chapters = {(v["book"], v["chapter"]) for v in verses}
    if len(books_chapters) == 1:
        book_name = verses[0]["bookName"]
        chapter = verses[0]["chapter"]
        vmin = min(v["v"] for v in verses)
        vmax = max(v["vEnd"] for v in verses)
        return format_ref(book_name, chapter, vmin, vEnd=vmax)
    return ", ".join(format_ref(v["bookName"], v["chapter"], v["v"], vEnd=v["vEnd"]) for v in verses)
