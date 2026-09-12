"""웹 서비스 진입점 (Docker/NAS 배포용). Werkzeug 개발서버 대신 waitress로 서빙한다."""
import os

from waitress import serve

from app.server import create_app

app = create_app(require_auth=True)


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8765"))
    serve(app, host=host, port=port)


if __name__ == "__main__":
    main()
