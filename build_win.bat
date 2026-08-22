@echo off
REM Windows용 .exe 빌드. Windows PC에서 실행하세요 (Mac에서는 실행 불가).
cd /d "%~dp0"

if not exist venv (
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt

if not exist app\data\bible.json (
  python scripts\build_bible_data.py
)
if not exist app\data\backgrounds_default.json (
  python scripts\generate_default_backgrounds.py
)
if not exist icons\icon.ico (
  python scripts\generate_icon.py
)

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
pyinstaller build.spec --noconfirm

echo.
echo 완료: dist\성경말씀PPT생성기\성경말씀PPT생성기.exe
