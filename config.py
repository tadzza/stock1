# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── 데이터베이스 ───────────────────────────────────────────
DATABASE_PATH = os.path.join(BASE_DIR, "data", "reports.db")

# ─── 브리핑 저장 경로 ───────────────────────────────────────
BRIEFING_DIR = os.path.join(BASE_DIR, "data", "briefings")

# ─── 크롤러 공통 설정 ───────────────────────────────────────
REQUEST_DELAY   = 1.5
REQUEST_TIMEOUT = 15
MAX_RETRIES     = 3
MAX_PAGES       = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://finance.naver.com/",
}

# ─── 스케줄러 ───────────────────────────────────────────────
SCHEDULER_HOUR   = 9
SCHEDULER_MINUTE = 0

# ─── Flask ──────────────────────────────────────────────────
FLASK_HOST  = "0.0.0.0"
FLASK_PORT  = 5000
FLASK_DEBUG = False
