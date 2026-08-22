#!/bin/bash
# dist/성경말씀PPT생성기.app 을 배포용 .dmg로 패키징한다.
# 먼저 build_mac.sh 로 .app을 최신 상태로 빌드해 둘 것.
set -e
cd "$(dirname "$0")"

APP_NAME="성경말씀PPT생성기"
APP_PATH="dist/${APP_NAME}.app"

if [ ! -d "$APP_PATH" ]; then
  echo "먼저 ./build_mac.sh 를 실행해 ${APP_PATH} 를 만들어주세요."
  exit 1
fi

STAGE=$(mktemp -d)
cp -R "$APP_PATH" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

rm -f "dist/${APP_NAME}.dmg"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "dist/${APP_NAME}.dmg"
rm -rf "$STAGE"

echo ""
echo "완료: dist/${APP_NAME}.dmg"
