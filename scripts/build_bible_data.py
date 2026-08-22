"""개역개정4판(구약+신약).txt 를 파싱해 app/data/bible.json 을 생성한다.

원본 라인 형식:
  창1:1 <천지 창조> 태초에 하나님이 천지를 창조하시니라
  신6:18-19 여호와께서 ...  (절 범위가 하나의 라인에 합쳐진 경우)

실행:
  python scripts/build_bible_data.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data_source" / "개역개정4판(구약+신약).txt"
OUT = ROOT / "app" / "data" / "bible.json"

# (약어, 전체이름, 권/장 정경순서)
BOOKS = [
    ("창", "창세기"), ("출", "출애굽기"), ("레", "레위기"), ("민", "민수기"), ("신", "신명기"),
    ("수", "여호수아"), ("삿", "사사기"), ("룻", "룻기"), ("삼상", "사무엘상"), ("삼하", "사무엘하"),
    ("왕상", "열왕기상"), ("왕하", "열왕기하"), ("대상", "역대상"), ("대하", "역대하"), ("스", "에스라"),
    ("느", "느헤미야"), ("에", "에스더"), ("욥", "욥기"), ("시", "시편"), ("잠", "잠언"),
    ("전", "전도서"), ("아", "아가"), ("사", "이사야"), ("렘", "예레미야"), ("애", "예레미야애가"),
    ("겔", "에스겔"), ("단", "다니엘"), ("호", "호세아"), ("욜", "요엘"), ("암", "아모스"),
    ("옵", "오바댜"), ("욘", "요나"), ("미", "미가"), ("나", "나훔"), ("합", "하박국"),
    ("습", "스바냐"), ("학", "학개"), ("슥", "스가랴"), ("말", "말라기"),
    ("마", "마태복음"), ("막", "마가복음"), ("눅", "누가복음"), ("요", "요한복음"), ("행", "사도행전"),
    ("롬", "로마서"), ("고전", "고린도전서"), ("고후", "고린도후서"), ("갈", "갈라디아서"), ("엡", "에베소서"),
    ("빌", "빌립보서"), ("골", "골로새서"), ("살전", "데살로니가전서"), ("살후", "데살로니가후서"),
    ("딤전", "디모데전서"), ("딤후", "디모데후서"), ("딛", "디도서"), ("몬", "빌레몬서"), ("히", "히브리서"),
    ("약", "야고보서"), ("벧전", "베드로전서"), ("벧후", "베드로후서"), ("요일", "요한일서"),
    ("요이", "요한이서"), ("요삼", "요한삼서"), ("유", "유다서"), ("계", "요한계시록"),
]
ABBR_TO_INFO = {abbr: {"name": name, "order": i} for i, (abbr, name) in enumerate(BOOKS)}
# 긴 약어(삼상, 고전 등)를 먼저 매칭하도록 길이 내림차순 정렬
ABBR_SORTED = sorted(ABBR_TO_INFO.keys(), key=len, reverse=True)

LINE_RE = re.compile(
    r"^(?P<abbr>" + "|".join(re.escape(a) for a in ABBR_SORTED) + r")"
    r"(?P<chapter>\d+):(?P<vstart>\d+)(-(?P<vend>\d+))?"
    r"\s+(?:<(?P<subtitle>[^>]*)>\s*)?(?P<text>.*)$"
)

# 원본 데이터 중 극소수(0.15%) 라인은 절 번호가 누락되어 있음. 대부분 <소제목>이
# 문장 중간에 삽입되며 잘려나간 앞 절의 연속(예: "삼상4:1 사무엘의 말이..." 다음
# "삼상4:이스라엘은 <..> 나가서...")이고, 일부(시편 권 구분 "제이권" 등)는
# 다음 절 앞에 붙는 표제다. 두 경우 모두 절 번호 없이 "약어+장:본문" 형태.
BROKEN_RE = re.compile(
    r"^(?P<abbr>" + "|".join(re.escape(a) for a in ABBR_SORTED) + r")"
    r"(?P<chapter>\d+):(?P<rest>.*)$"
)


def main():
    raw = SRC.read_bytes().decode("euc-kr", errors="strict")
    lines = raw.splitlines()

    verses = {abbr: {} for abbr in ABBR_TO_INFO}
    still_unmatched = []
    last_unit = None
    last_book = None
    last_chapter = None
    pending_prefix = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = LINE_RE.match(line)
        if m:
            abbr = m.group("abbr")
            chapter = int(m.group("chapter"))
            vstart = int(m.group("vstart"))
            vend = int(m.group("vend")) if m.group("vend") else vstart
            subtitle = m.group("subtitle")
            if pending_prefix:
                subtitle = pending_prefix if not subtitle else f"{pending_prefix} {subtitle}"
                pending_prefix = None
            text = m.group("text").strip()

            unit = {"v": vstart, "vEnd": vend, "subtitle": subtitle, "text": text}
            verses[abbr].setdefault(str(chapter), []).append(unit)
            last_unit, last_book, last_chapter = unit, abbr, chapter
            continue

        bm = BROKEN_RE.match(line)
        if not bm:
            still_unmatched.append(line)
            continue

        abbr = bm.group("abbr")
        chapter = int(bm.group("chapter"))
        # 문장 중간에 낀 <소제목>은 본문이 아니므로 통째로 제거(내부 텍스트도 버림)
        rest = re.sub(r"\s*<[^>]*>\s*", " ", bm.group("rest")).strip()

        if last_unit is not None and last_book == abbr and last_chapter == chapter:
            last_unit["text"] = (last_unit["text"] + " " + rest).strip()
        else:
            pending_prefix = rest

    if still_unmatched:
        print(f"[경고] 매칭 실패 라인 {len(still_unmatched)}건 (앞 5개 출력):")
        for l in still_unmatched[:5]:
            print("  ", l)

    books_meta = [
        {"abbr": abbr, "name": info["name"], "order": info["order"]}
        for abbr, info in sorted(ABBR_TO_INFO.items(), key=lambda kv: kv[1]["order"])
    ]

    total_units = sum(len(v) for chs in verses.values() for v in chs.values())
    print(f"총 절(라인) 유닛 수: {total_units}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump({"books": books_meta, "verses": verses}, f, ensure_ascii=False, indent=None)
    print(f"저장 완료: {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
