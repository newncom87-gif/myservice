"""로컬 전용 Flask API + 정적 프론트엔드 서빙."""
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from . import backgrounds, bible_data as bd, compose, paths
from . import fonts as font_store
from . import themes as theme_store
from . import projects as project_store
from . import ppt_builder


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
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

    # ---- 배경이미지 ----
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
        return send_from_directory(paths.uploads_dir(), filename)

    @app.delete("/api/backgrounds/user/<path:filename>")
    def api_backgrounds_delete(filename):
        p = paths.uploads_dir() / filename
        if p.exists():
            p.unlink()
        return jsonify({"ok": True})

    # ---- 테마(표지/본문 서식) ----
    @app.get("/api/themes")
    def api_themes_list():
        return jsonify(theme_store.load_themes())

    @app.post("/api/themes")
    def api_themes_save():
        data = request.get_json(force=True) or {}
        try:
            return jsonify(theme_store.save_theme(data))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.delete("/api/themes/<name>")
    def api_themes_delete(name):
        return jsonify(theme_store.delete_theme(name))

    # ---- 작업(구절/분배/배경/테마 전체 상태) ----
    @app.get("/api/projects")
    def api_projects_list():
        return jsonify(project_store.load_projects())

    @app.post("/api/projects")
    def api_projects_save():
        data = request.get_json(force=True) or {}
        try:
            return jsonify(project_store.save_project(data))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.delete("/api/projects/<name>")
    def api_projects_delete(name):
        return jsonify(project_store.delete_project(name))

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
    create_app().run(host="127.0.0.1", port=8765, debug=True)
