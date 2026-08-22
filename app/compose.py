"""구절 블록 여러 개를 조합하고, 슬라이드 단위로 분배하는 로직."""
from . import bible_data as bd


def resolve_blocks(blocks):
    """구절 블록 목록을 받아 (flat_verses, block_refs) 반환.

    blocks: [{book, startChapter, startVerse, endChapter, endVerse}, ...]
    flat_verses: 전체 구절 유닛을 블록 순서대로 이어붙인 리스트
    block_refs: 각 블록의 참조 문자열 리스트 (표지 표기용, 예: "창세기 12:2~3")
    """
    flat_verses = []
    block_refs = []
    for i, blk in enumerate(blocks):
        abbr = blk["book"]
        sc, sv = int(blk["startChapter"]), int(blk["startVerse"])
        ec, ev = int(blk["endChapter"]), int(blk["endVerse"])
        units = bd.resolve_range(abbr, sc, sv, ec, ev)
        if not units:
            raise ValueError(f"블록 {i+1}: 해당 범위에 구절이 없습니다")
        for u in units:
            u = dict(u)
            u["blockIndex"] = i
            flat_verses.append(u)
        book_name = bd.get_book(abbr)["name"]
        block_refs.append(bd.format_ref(book_name, sc, sv, end_chapter=ec, end_v=ev))
    return flat_verses, block_refs


def compute_slides(flat_verses, default_group_size=2, overrides=None):
    """flat_verses를 슬라이드 단위 리스트로 분배한다.

    overrides: [n1, n2, ...] 앞 슬라이드부터 순서대로 적용할 구절 수. 리스트를
    벗어나는 뒤쪽 슬라이드는 default_group_size 로 채운다.
    """
    overrides = overrides or []
    default_group_size = max(1, int(default_group_size))

    slides = []
    idx = 0
    n = len(flat_verses)
    slide_no = 0
    while idx < n:
        override_val = overrides[slide_no] if slide_no < len(overrides) else None
        size = int(override_val) if override_val not in (None, "") else default_group_size
        size = max(1, size)
        slides.append(flat_verses[idx: idx + size])
        idx += size
        slide_no += 1
    return slides
