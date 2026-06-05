# models/database.py
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from config import DATABASE_PATH
import os

logger = logging.getLogger(__name__)

os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_name    TEXT    NOT NULL,
                title         TEXT    NOT NULL,
                firm          TEXT    NOT NULL,
                pub_date      TEXT    NOT NULL,
                download_url  TEXT,
                opinion       TEXT,
                target_price  TEXT,
                analyst       TEXT,
                category      TEXT    DEFAULT '기업분석',
                created_at    TEXT    DEFAULT (datetime('now','localtime')),
                UNIQUE (stock_name, title, firm, pub_date)
            );

            CREATE INDEX IF NOT EXISTS idx_pub_date   ON reports(pub_date);
            CREATE INDEX IF NOT EXISTS idx_stock_name ON reports(stock_name);
            CREATE INDEX IF NOT EXISTS idx_firm       ON reports(firm);

            CREATE TABLE IF NOT EXISTS crawl_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at      TEXT    DEFAULT (datetime('now','localtime')),
                source      TEXT,
                new_count   INTEGER,
                total_count INTEGER,
                status      TEXT,
                message     TEXT
            );
        """)
    logger.info("DB 초기화 완료: %s", DATABASE_PATH)


def insert_reports(reports: list) -> int:
    if not reports:
        return 0
    sql = """
        INSERT OR IGNORE INTO reports
            (stock_name, title, firm, pub_date, download_url,
             opinion, target_price, analyst, category)
        VALUES
            (:stock_name, :title, :firm, :pub_date, :download_url,
             :opinion, :target_price, :analyst, :category)
    """
    with get_connection() as conn:
        before = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        conn.executemany(sql, reports)
        after  = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    return after - before


def log_crawl(source, new_count, total_count, status, message=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO crawl_log (source, new_count, total_count, status, message) "
            "VALUES (?, ?, ?, ?, ?)",
            (source, new_count, total_count, status, message)
        )


def get_recent_reports(days=7, firm=None, keyword=None, page=1, per_page=30):
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conditions = ["pub_date >= ?"]
    params = [since]

    if firm and firm != "전체":
        conditions.append("firm = ?")
        params.append(firm)

    if keyword:
        conditions.append("(stock_name LIKE ? OR title LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like])

    where = "WHERE " + " AND ".join(conditions)

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM reports {where}", params
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT * FROM reports {where} "
            f"ORDER BY pub_date DESC, id DESC "
            f"LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()

    return {
        "reports":     [dict(r) for r in rows],
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": max(1, -(-total // per_page)),
    }


def get_distinct_firms():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT firm FROM reports ORDER BY firm"
        ).fetchall()
    return [r[0] for r in rows]


def get_today_reports():
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM reports WHERE pub_date = ? ORDER BY firm, stock_name",
            (today,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_crawl_logs(limit=20):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM crawl_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        today = conn.execute(
            "SELECT COUNT(*) FROM reports WHERE pub_date = date('now','localtime')"
        ).fetchone()[0]
        week = conn.execute(
            "SELECT COUNT(*) FROM reports "
            "WHERE pub_date >= date('now','-7 days','localtime')"
        ).fetchone()[0]
        by_firm = conn.execute(
            "SELECT firm, COUNT(*) as cnt FROM reports "
            "WHERE pub_date >= date('now','-7 days','localtime') "
            "GROUP BY firm ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
    return {
        "total":   total,
        "today":   today,
        "week":    week,
        "by_firm": [dict(r) for r in by_firm],
    }
