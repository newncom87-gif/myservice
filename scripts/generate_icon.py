"""앱 아이콘(.icns / .ico) 생성. 십자가 심볼 + 남색 그라데이션.

실행: python scripts/generate_icon.py
macOS에서만 .icns까지 만들어짐(iconutil 필요). .ico는 모든 OS에서 생성됨.
"""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "icons"
SIZE = 1024


def make_base_image():
    base = Image.linear_gradient("L").resize((SIZE, SIZE))
    img = ImageOps.colorize(base, black=(10, 16, 34), white=(30, 46, 84)).convert("RGB")

    draw = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2
    bar_w = int(SIZE * 0.11)
    v_h = int(SIZE * 0.62)
    h_w = int(SIZE * 0.44)
    color = (242, 169, 59)  # 앱 포인트 컬러(F2A93B)와 통일

    draw.rounded_rectangle(
        [cx - bar_w // 2, cy - v_h // 2, cx + bar_w // 2, cy + v_h // 2],
        radius=bar_w // 3, fill=color,
    )
    draw.rounded_rectangle(
        [cx - h_w // 2, cy - v_h // 2 + int(v_h * 0.22) - bar_w // 2,
         cx + h_w // 2, cy - v_h // 2 + int(v_h * 0.22) + bar_w // 2],
        radius=bar_w // 3, fill=color,
    )
    return img


def make_ico(img):
    ico_path = OUT_DIR / "icon.ico"
    img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"저장: {ico_path}")


def make_icns(img):
    if sys.platform != "darwin" or not shutil.which("iconutil"):
        print("iconutil 없음(macOS 전용) - .icns 생략")
        return
    iconset = OUT_DIR / "icon.iconset"
    iconset.mkdir(exist_ok=True)
    specs = [16, 32, 64, 128, 256, 512, 1024]
    for s in specs:
        img.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
        if s <= 512:
            img.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(OUT_DIR / "icon.icns")], check=True)
    shutil.rmtree(iconset)
    print(f"저장: {OUT_DIR / 'icon.icns'}")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    img = make_base_image()
    make_ico(img)
    make_icns(img)


if __name__ == "__main__":
    main()
