"""시스템에 설치된 폰트 목록 조회.

tkinter는 (특히 macOS Aqua에서) 메인 스레드가 아닌 곳에서 호출하면 멈추는
문제가 있다. Flask는 별도 백그라운드 스레드에서 돌기 때문에 요청이 올 때마다
조회하면 안 되고, create_app() 호출 시점(항상 메인 스레드)에 한 번만 조회해
캐싱해 둔다.
"""

_FALLBACK = ["맑은 고딕", "Apple SD Gothic Neo", "Arial", "Malgun Gothic", "Noto Sans KR"]


def get_system_fonts():
    try:
        import tkinter
        import tkinter.font

        root = tkinter.Tk()
        root.withdraw()
        try:
            fonts = sorted({f for f in tkinter.font.families() if f and not f.startswith("@")}, key=str.lower)
        finally:
            root.destroy()
        return fonts or _FALLBACK
    except Exception:
        return _FALLBACK
