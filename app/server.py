"""Flask API + 정적 프론트엔드 서빙 (데스크톱/웹 공용).

데스크톱 앱(main.py)은 로컬 1인 사용자 전제이므로 로그인 없이 고정된 로컬
계정으로 동작하고(create_app(require_auth=False)), 웹 배포(wsgi.py)는 팀원별
로그인을 요구한다(create_app(require_auth=True), 기본값).
"""
import json
import os
import secrets
import uuid
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_file, send_from_directory, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from . import backgrounds, bible_data as bd, compose, db, paths
from . import fonts as font_store
from . import themes as theme_store
from . import projects as project_store
from . import users as user_store
from . import ppt_builder

PUBLIC_PATHS = {"/login", "/api/login"}
LOCAL_USERNAME = "desktop-local"


def _get_or_create_secret_key():
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    p = paths.secret_key_path()
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    key = secrets.token_hex(32)
    p.write_text(key, encoding="utf-8")
    return key


def _ensure_local_user():
    """데스크톱(로그인 없음) 모드에서 테마/작업을 저장할 고정 로컬 계정을 보장한다."""
    row = user_store.get_by_username(LOCAL_USERNAME)
    if row:
        return row["id"]
    return user_store.create_user(LOCAL_USERNAME, secrets.token_hex(16))


def _migrate_legacy_json(user_id):
    """구버전(로그인 도입 이전) themes.json/projects.json을 SQLite로 1회 이전한다."""
    for filename, store in (("themes.json", theme_store), ("projects.json", project_store)):
        legacy_path = paths.user_data_dir() / filename
        if not legacy_path.exists():
            continue
        try:
            items = json.loads(legacy_path.read_text(encoding="utf-8"))
            save_fn = store.save_theme if store is theme_store else store.save_project
            for item in items:
                save_fn(user_id, item)
        finally:
            legacy_path.rename(legacy_path.with_suffix(".json.migrated"))


def create_app(require_auth=True):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    # nginx 등 리버스 프록시가 /bible 같은 하위 경로로 마운트할 때, X-Forwarded-Prefix
    # 헤더를 SCRIPT_NAME으로 반영해 url_for()가 생성하는 redirect Location이 그
    # 경로를 포함하도록 한다. 헤더가 없으면(데스크톱/로컬 직접 접속) 그대로 무시된다.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config["SECRET_KEY"] = _get_or_create_secret_key()
    db.init_db()

    if require_auth:
        from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user

        class WebUser(UserMixin):
            def __init__(self, row):
                self.id = row["id"]
                self.username = row["username"]

        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            row = user_store.get_by_id(int(user_id))
            return WebUser(row) if row else None

        @app.before_request
        def require_login():
            if request.path.startswith("/static/") or request.path in PUBLIC_PATHS:
                return None
            if current_user.is_authenticated:
                return None
            if request.path == "/":
                return redirect(url_for("login_page"))
            return jsonify({"error": "로그인이 필요합니다"}), 401

        @app.get("/login")
        def login_page():
            if current_user.is_authenticated:
                return redirect(url_for("index"))
            return app.send_static_file("login.html")

        @app.post("/api/login")
        def api_login():
            data = request.get_json(force=True) or {}
            row = user_store.verify_password(data.get("username", ""), data.get("password", ""))
            if not row:
                return jsonify({"error": "아이디 또는 비밀번호가 올바르지 않습니다"}), 401
            login_user(WebUser(row), remember=True)
            return jsonify({"ok": True})

        @app.post("/api/logout")
        def api_logout():
            logout_user()
            return jsonify({"ok": True})

        def current_user_id():
            return current_user.id
    else:
        local_user_id = _ensure_local_user()
        _migrate_legacy_json(local_user_id)

        def current_user_id():
            return local_user_id

    # tkinter는 메인 스레드에서만 안전하므로(create_app()은 항상 메인 스레드에서
    # 호출됨), 요청마다 조회하지 않고 여기서 한 번만 캐싱한다.
    system_fonts = font_store.get_system_fonts()

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/fonts")
    def api_fonts():
        return jsonify(system_fonts)

    # ---- 성경 데이터 ----
    @app.get("/api/books")
    def api_books():
        return jsonify(bd.get_books())

    @app.get("/api/chapters")
    def api_chapters():
        book = request.args.get("book", "")
        try:
            return jsonify(bd.get_chapters(book))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.get("/api/max_verse")
    def api_max_verse():
        book = request.args.get("book", "")
        try:
            chapter = int(request.args.get("chapter", ""))
            return jsonify({"maxVerse": bd.get_max_verse(book, chapter)})
        except (ValueError, TypeError) as e:
            return jsonify({"error": str(e)}), 400

    # ---- 구절 조합 & 슬라이드 분배 (프리뷰용) ----
    @app.post("/api/compose")
    def api_compose():
        data = request.get_json(force=True) or {}
        blocks = data.get("blocks", [])
        default_group_size = data.get("defaultGroupSize", 2)
        overrides = data.get("overrides", [])
        if not blocks:
            return jsonify({"blockRefs": [], "totalVerseUnits": 0, "slides": []})
        try:
            flat, block_refs = compose.resolve_blocks(blocks)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        slides = compose.compute_slides(flat, default_group_size, overrides)
        slides_out = []
        for i, verses in enumerate(slides):
            slides_out.append({"index": i, "verses": verses, "refText": bd.format_slide_ref(verses)})
        return jsonify({"blockRefs": block_refs, "totalVerseUnits": len(flat), "slides": slides_out})

    # ---- 배경이미지 (로그인한 모든 사용자가 공동으로 사용/관리) ----
    @app.get("/api/backgrounds")
    def api_backgrounds():
        return jsonify({"default": backgrounds.list_default(), "user": backgrounds.list_user()})

    @app.post("/api/backgrounds/upload")
    def api_backgrounds_upload():
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"error": "파일이 없습니다"}), 400
        ext = Path(file.filename).suffix.lower()
        if ext not in backgrounds.ALLOWED_EXT:
            return jsonify({"error": "지원하지 않는 이미지 형식입니다 (jpg/png/webp)"}), 400
        filename = f"{uuid.uuid4().hex}{ext}"
        file.save(paths.uploads_dir() / filename)
        return jsonify({"id": filename, "name": Path(file.filename).stem, "file": filename})

    @app.get("/user-bg/<path:filename>")
    def user_bg(filename):
        return send_from_directory(paths.uploads_dir(), Path(filename).name)

    @app.delete("/api/backgrounds/user/<path:filename>")
    def api_backgrounds_delete(filename):
        p = paths.uploads_dir() / Path(filename).name
        if p.exists():
            p.unlink()
        return jsonify({"ok": True})

    # ---- 테마(표지/본문 서식, 계정별로 분리) ----
    @app.get("/api/themes")
    def api_themes_list():
        return jsonify(theme_store.load_themes(current_user_id()))

    @app.post("/api/themes")
    def api_themes_save():
        data = request.get_json(force=True) or {}
        try:
            return jsonify(theme_store.save_theme(current_user_id(), data))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.delete("/api/themes/<name>")
    def api_themes_delete(name):
        return jsonify(theme_store.delete_theme(current_user_id(), name))

    # ---- 작업(구절/분배/배경/테마 전체 상태, 계정별로 분리) ----
    @app.get("/api/projects")
    def api_projects_list():
        return jsonify(project_store.load_projects(current_user_id()))

    @app.post("/api/projects")
    def api_projects_save():
        data = request.get_json(force=True) or {}
        try:
            return jsonify(project_store.save_project(current_user_id(), data))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.delete("/api/projects/<name>")
    def api_projects_delete(name):
        return jsonify(project_store.delete_project(current_user_id(), name))

    # ---- PPT 생성 ----
    @app.post("/api/generate")
    def api_generate():
        spec = request.get_json(force=True) or {}
        try:
            buf = ppt_builder.build_presentation(spec)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return send_file(
            buf,
            as_attachment=True,
            download_name="성경말씀.pptx",
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    return app


if __name__ == "__main__":
    create_app(require_auth=False).run(host="127.0.0.1", port=8765, debug=True)
