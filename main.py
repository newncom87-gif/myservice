"""성경말씀 PPT 생성기 - 데스크톱 앱 진입점.

Flask 서버를 백그라운드 스레드에서 임의의 빈 포트로 띄우고, pywebview로 그
포트를 가리키는 독립 창을 연다. 사용자에게는 브라우저나 서버가 전혀 노출되지
않고 일반 데스크톱 앱처럼 보인다.
"""
import base64
import sys
import threading
from pathlib import Path

# PyInstaller로 패키징됐을 때도 app 패키지를 찾을 수 있도록 경로 보정
sys.path.insert(0, str(Path(__file__).resolve().parent))

import webview
from werkzeug.serving import make_server

from app.server import create_app


class ServerThread(threading.Thread):
    def __init__(self, flask_app):
        super().__init__(daemon=True)
        self.server = make_server("127.0.0.1", 0, flask_app)
        self.port = self.server.server_port

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


class Api:
    """pywebview 창의 브라우저(WKWebView 등)는 HTML5 <a download> 방식의
    다운로드를 지원하지 않는 경우가 많아, 파일 저장은 이 API를 통해 네이티브
    "다른 이름으로 저장" 대화상자로 처리한다. window는 창 생성 후 채워진다.
    """

    def __init__(self):
        self.window = None

    def save_pptx(self, base64_data, filename):
        if self.window is None:
            return {"ok": False, "error": "창이 아직 준비되지 않았습니다"}
        result = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=filename,
            file_types=("PowerPoint 파일 (*.pptx)",),
        )
        if not result:
            return {"ok": False, "cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else result
        if not path:
            return {"ok": False, "cancelled": True}
        try:
            with open(path, "wb") as f:
                f.write(base64.b64decode(base64_data))
        except OSError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "path": path}


def main():
    flask_app = create_app()
    server_thread = ServerThread(flask_app)
    server_thread.start()

    api = Api()
    window = webview.create_window(
        "성경말씀 PPT 생성기",
        f"http://127.0.0.1:{server_thread.port}",
        width=1760,
        height=1040,
        min_size=(1280, 780),
        js_api=api,
    )
    api.window = window
    webview.start()
    server_thread.shutdown()


if __name__ == "__main__":
    main()
