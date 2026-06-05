# app.py
import os
import logging
import atexit
from flask import (Flask, render_template, request,
                   jsonify, send_from_directory, abort)
from models.database import (
    init_db, get_recent_reports, get_distinct_firms,
    get_stats, get_crawl_logs, get_today_reports
)
from scheduler.jobs import create_scheduler
from crawler.manager import run_all_crawlers
from briefing.generator import generate_daily_briefing, BRIEFING_DIR
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

init_db()
scheduler = create_scheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown(wait=False))
logger.info("APScheduler 시작 완료")


@app.route("/")
def index():
    firm    = request.args.get("firm", "전체")
    keyword = request.args.get("q", "").strip()
    page    = int(request.args.get("page", 1))

    data  = get_recent_reports(days=7, firm=firm,
                               keyword=keyword or None, page=page)
    firms = ["전체"] + get_distinct_firms()
    stats = get_stats()

    return render_template(
        "index.html",
        reports      = data["reports"],
        total        = data["total"],
        total_pages  = data["total_pages"],
        current_page = data["page"],
        firms        = firms,
        selected_firm= firm,
        keyword      = keyword,
        stats        = stats,
    )


@app.route("/search")
def search():
    keyword = request.args.get("q", "").strip()
    page    = int(request.args.get("page", 1))

    if not keyword:
        return render_template("search.html", reports=[], keyword="", total=0,
                               total_pages=1, current_page=1)

    data = get_recent_reports(days=90, keyword=keyword, page=page)
    return render_template(
        "search.html",
        reports      = data["reports"],
        keyword      = keyword,
        total        = data["total"],
        total_pages  = data["total_pages"],
        current_page = data["page"],
    )


@app.route("/briefing")
def briefing_latest():
    reports = get_today_reports()
    firms   = {}
    for r in reports:
        firms.setdefault(r["firm"], []).append(r)
    return render_template("briefing.html", firms=firms, reports=reports)


@app.route("/briefing/<date_str>")
def briefing_by_date(date_str: str):
    filename = f"briefing_{date_str}.html"
    if not os.path.exists(os.path.join(BRIEFING_DIR, filename)):
        abort(404)
    return send_from_directory(BRIEFING_DIR, filename)


@app.route("/api/reports")
def api_reports():
    firm    = request.args.get("firm")
    keyword = request.args.get("q")
    page    = int(request.args.get("page", 1))
    days    = int(request.args.get("days", 7))
    return jsonify(get_recent_reports(days=days, firm=firm,
                                     keyword=keyword, page=page))


@app.route("/api/crawl", methods=["POST"])
def api_crawl():
    logger.info("수동 크롤링 요청 수신")
    try:
        result = run_all_crawlers()
        generate_daily_briefing()
        return jsonify({"status": "success", **result})
    except Exception as e:
        logger.error("수동 크롤링 오류: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/logs")
def api_logs():
    return jsonify(get_crawl_logs())


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
