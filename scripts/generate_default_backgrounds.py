"""저작권 걱정 없는 기본 배경이미지 세트를 Pillow로 생성한다.

텍스트 가독성을 위해 대비가 크지 않고 은은한 그라데이션/비네트 위주로 구성.
실행: python scripts/generate_default_backgrounds.py
"""
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "app" / "static" / "backgrounds" / "default"
MANIFEST = ROOT / "app" / "data" / "backgrounds_default.json"

SIZE = (1920, 1080)


def linear_vertical(size, top_color, bottom_color):
    base = Image.linear_gradient("L").resize(size)
    return ImageOps.colorize(base, black=top_color, white=bottom_color).convert("RGB")


def linear_diagonal(size, color1, color2):
    # 회전 후 크롭한 영역이 검게 채워진 모서리(필 영역)를 침범하지 않으려면
    # 원본 정사각형 한 변 길이가 (w+h) 이상이어야 한다.
    w, h = size
    s = w + h + 100
    base = Image.linear_gradient("L").resize((s, s))
    rotated = base.rotate(45, expand=True, resample=Image.BICUBIC)
    rw, rh = rotated.size
    left = (rw - w) // 2
    top = (rh - h) // 2
    cropped = rotated.crop((left, top, left + w, top + h))
    return ImageOps.colorize(cropped, black=color1, white=color2).convert("RGB")


def vignette(size, base_color, edge_color, strength=0.75):
    img = Image.new("RGB", size, base_color)
    radial = Image.radial_gradient("L").resize(size)  # 중심 0(검정) ~ 모서리 255(흰색)
    alpha = radial.point(lambda p: int(min(255, p * strength)))
    overlay = Image.new("RGB", size, edge_color)
    return Image.composite(overlay, img, alpha)


PRESETS = [
    {
        "id": "navy-fade",
        "name": "차분한 네이비",
        "make": lambda: linear_vertical(SIZE, (18, 28, 54), (4, 8, 18)),
    },
    {
        "id": "deep-charcoal",
        "name": "딥 차콜",
        "make": lambda: vignette(SIZE, (48, 48, 52), (10, 10, 12), strength=0.85),
    },
    {
        "id": "warm-sunset",
        "name": "따뜻한 노을",
        "make": lambda: linear_vertical(SIZE, (92, 42, 30), (30, 14, 26)),
    },
    {
        "id": "royal-purple",
        "name": "로열 퍼플",
        "make": lambda: vignette(SIZE, (54, 30, 84), (14, 8, 26), strength=0.8),
    },
    {
        "id": "forest-green",
        "name": "차분한 포레스트",
        "make": lambda: linear_vertical(SIZE, (18, 52, 40), (6, 18, 16)),
    },
    {
        "id": "soft-sky",
        "name": "은은한 하늘",
        "make": lambda: linear_vertical(SIZE, (120, 158, 196), (52, 78, 112)),
    },
    {
        "id": "parchment",
        "name": "따뜻한 파피루스",
        "make": lambda: vignette(SIZE, (230, 214, 182), (176, 150, 104), strength=0.5),
    },
    {
        "id": "wine",
        "name": "와인 레드",
        "make": lambda: linear_diagonal(SIZE, (74, 16, 26), (24, 6, 12)),
    },
    {
        "id": "teal-glow",
        "name": "틸 글로우",
        "make": lambda: vignette(SIZE, (16, 62, 66), (4, 16, 20), strength=0.8),
    },
    {
        "id": "gold-black",
        "name": "골드 블랙",
        "make": lambda: linear_vertical(SIZE, (40, 32, 10), (10, 8, 4)),
    },
]


# 실사 배경 사진(Pexels License - 상업적 이용 무료, 출처 표시 불필요). 이미지 파일
# 자체는 이 스크립트가 만들지 않고 이미 app/static/backgrounds/default/ 에 있어야
# 한다(1920x1080 JPEG). source는 출처 기록용 메타데이터.
PHOTO_BACKGROUNDS = [
    {"id": "church-interior-01", "name": "교회 내부 1", "file": "church-interior-01.jpg", "source": "https://www.pexels.com/photo/modest-christian-church-interior-16000635/"},
    {"id": "church-interior-02", "name": "교회 내부 2", "file": "church-interior-02.jpg", "source": "https://www.pexels.com/photo/interior-of-church-9221328/"},
    {"id": "wooden-cross-sky", "name": "나무 십자가", "file": "wooden-cross-sky.jpg", "source": "https://www.pexels.com/photo/brown-wooden-cross-208371/"},
    {"id": "bible-with-cross", "name": "성경과 십자가", "file": "bible-with-cross.jpg", "source": "https://www.pexels.com/photo/a-bible-with-wooden-cross-4330070/"},
    {"id": "open-bible-dark", "name": "펼쳐진 성경 (어두운 톤)", "file": "open-bible-dark.jpg", "source": "https://www.pexels.com/photo/open-bible-2294878/"},
    {"id": "open-bible-warm", "name": "펼쳐진 성경 (따뜻한 톤)", "file": "open-bible-warm.jpg", "source": "https://www.pexels.com/photo/close-up-of-open-bible-on-table-11696719/"},
    {"id": "stained-glass-01", "name": "스테인드글라스 1", "file": "stained-glass-01.jpg", "source": "https://www.pexels.com/photo/a-stained-glass-church-window-with-a-beautiful-design-8674185/"},
    {"id": "stained-glass-02", "name": "스테인드글라스 2", "file": "stained-glass-02.jpg", "source": "https://www.pexels.com/photo/low-angle-view-of-stained-glass-window-248091/"},
    {"id": "candle-dark", "name": "촛불", "file": "candle-dark.jpg", "source": "https://www.pexels.com/photo/lighted-candle-in-dark-room-5843608/"},
    {"id": "praying-hands-bible", "name": "기도하는 손", "file": "praying-hands-bible.jpg", "source": "https://www.pexels.com/photo/belief-bible-book-business-267559/"},
    {"id": "worship-silhouette-01", "name": "찬양 실루엣 1", "file": "worship-silhouette-01.jpg", "source": "https://www.pexels.com/photo/silhouette-of-a-man-worshiping-13899663/"},
    {"id": "worship-silhouette-02", "name": "찬양 실루엣 2", "file": "worship-silhouette-02.jpg", "source": "https://www.pexels.com/photo/silhouette-photo-of-person-raising-hands-1005198/"},
    {"id": "godrays-clouds", "name": "빛줄기(구름)", "file": "godrays-clouds.jpg", "source": "https://www.pexels.com/photo/sunbeams-behind-clouds-on-sky-17811024/"},
    {"id": "sunrise-clouds", "name": "일출 하늘", "file": "sunrise-clouds.jpg", "source": "https://www.pexels.com/photo/cloudy-sky-at-sunrise-in-rays-of-sun-5459411/"},
    {"id": "cross-sunset-01", "name": "십자가와 노을 1", "file": "cross-sunset-01.jpg", "source": "https://www.pexels.com/photo/cross-during-sunset-20889059/"},
    {"id": "cross-sunset-02", "name": "십자가와 노을 2", "file": "cross-sunset-02.jpg", "source": "https://www.pexels.com/photo/silhouette-of-cross-on-mountain-under-cloudy-sky-during-sunset-10996743/"},
    {"id": "wood-texture-dark", "name": "어두운 나무 질감", "file": "wood-texture-dark.jpg", "source": "https://www.pexels.com/photo/6373386/"},
    {"id": "stone-texture", "name": "돌 질감", "file": "stone-texture.jpg", "source": "https://www.pexels.com/photo/9497822/"},
    {"id": "dove-sky", "name": "비둘기(성령)", "file": "dove-sky.jpg", "source": "https://www.pexels.com/photo/white-dove-flying-19915968/"},
    {"id": "communion-bread-wine", "name": "성찬식(빵과 포도주)", "file": "communion-bread-wine.jpg", "source": "https://www.pexels.com/photo/a-person-holding-a-bread-and-wine-10293695/"},
    {"id": "baptism-lake", "name": "세례", "file": "baptism-lake.jpg", "source": "https://www.pexels.com/photo/a-woman-being-baptized-in-a-lake-6672761/"},
    {"id": "mountain-sunrise", "name": "산 일출", "file": "mountain-sunrise.jpg", "source": "https://www.pexels.com/photo/silhouette-of-mountain-under-cloudy-sky-during-sunset-4276431/"},
    {"id": "forest-path-light", "name": "숲속 빛줄기 오솔길", "file": "forest-path-light.jpg", "source": "https://www.pexels.com/photo/misty-sunlight-through-tall-forest-trees-36930289/"},
    {"id": "church-exterior-cloudy", "name": "예배당 외관", "file": "church-exterior-cloudy.jpg", "source": "https://www.pexels.com/photo/photo-of-old-church-building-under-cloudy-sky-2886268/"},
    {"id": "praying-hands-closeup", "name": "기도하는 손 클로즈업", "file": "praying-hands-closeup.jpg", "source": "https://www.pexels.com/photo/close-up-of-hands-257037/"},
    {"id": "bible-coffee-desk", "name": "성경과 커피", "file": "bible-coffee-desk.jpg", "source": "https://www.pexels.com/photo/cozy-desk-with-coffee-books-and-plants-31763922/"},
    {"id": "bell-tower", "name": "교회 종탑", "file": "bell-tower.jpg", "source": "https://www.pexels.com/photo/church-bell-tower-16820088/"},
    {"id": "church-podium", "name": "강대상", "file": "church-podium.jpg", "source": "https://www.pexels.com/photo/podium-with-a-microphone-inside-a-church-17492045/"},
    {"id": "cross-necklace-bw", "name": "십자가 목걸이", "file": "cross-necklace-bw.jpg", "source": "https://www.pexels.com/photo/man-wearing-cross-necklace-19622309/"},
    {"id": "calm-lake-sunset", "name": "잔잔한 호수 노을", "file": "calm-lake-sunset.jpg", "source": "https://www.pexels.com/photo/serene-sunset-over-calm-lake-reflection-30755997/"},
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for preset in PRESETS:
        img = preset["make"]()
        filename = f"{preset['id']}.jpg"
        img.save(OUT_DIR / filename, quality=90)
        manifest.append({"id": preset["id"], "name": preset["name"], "file": filename})
        print(f"생성: {filename}")

    missing = [p for p in PHOTO_BACKGROUNDS if not (OUT_DIR / p["file"]).exists()]
    if missing:
        print(f"[경고] 다음 실사 배경 파일이 없어 매니페스트에서 제외됨: {[p['file'] for p in missing]}")
    manifest += [p for p in PHOTO_BACKGROUNDS if p not in missing]

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"매니페스트 저장: {MANIFEST} (그라데이션 {len(PRESETS)} + 실사 {len(manifest) - len(PRESETS)})")


if __name__ == "__main__":
    main()
