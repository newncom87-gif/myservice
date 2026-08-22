#!/bin/bash
# macOS용 .app 빌드. 이 Mac에서 실행하세요.
set -e
cd "$(dirname "$0")"

if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

# 성경 데이터 / 기본 배경 / 아이콘이 없으면 생성
[ -f app/data/bible.json ] || python scripts/build_bible_data.py
[ -f app/data/backgrounds_default.json ] || python scripts/generate_default_backgrounds.py
[ -f icons/icon.icns ] || python scripts/generate_icon.py

rm -rf build dist
pyinstaller build.spec --noconfirm

echo ""
echo "완료: dist/성경말씀PPT생성기.app"
echo "다른 Mac에 배포 시 Gatekeeper가 '확인되지 않은 개발자' 경고를 띄울 수 있습니다."
echo "그 경우 앱을 우클릭 후 '열기'를 선택하면 실행할 수 있습니다."
