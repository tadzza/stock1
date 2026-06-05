# crawler/manager.py
import logging
from .naver_crawler import NaverCompanyCrawler, NaverIndustryCrawler
from models.database import insert_reports, log_crawl

logger = logging.getLogger(__name__)

CRAWLERS = [
    NaverCompanyCrawler,
    NaverIndustryCrawler,
]


def run_all_crawlers() -> dict:
    total_new     = 0
    total_fetched = 0
    details       = []

    for CrawlerClass in CRAWLERS:
        crawler = CrawlerClass()
        logger.info("=== [%s] 크롤링 시작 ===", crawler.name)
        try:
            reports = crawler.fetch()
            new_cnt = insert_reports(reports)
            log_crawl(
                source      = crawler.name,
                new_count   = new_cnt,
                total_count = len(reports),
                status      = "success",
                message     = f"총 {len(reports)}건 수집, {new_cnt}건 신규 저장"
            )
            total_new     += new_cnt
            total_fetched += len(reports)
            details.append({
                "crawler": crawler.name,
                "fetched": len(reports),
                "new":     new_cnt,
                "status":  "success",
            })
            logger.info("[%s] 완료 — 수집 %d건 / 신규 %d건",
                        crawler.name, len(reports), new_cnt)
        except Exception as e:
            log_crawl(
                source      = crawler.name,
                new_count   = 0,
                total_count = 0,
                status      = "error",
                message     = str(e),
            )
            details.append({
                "crawler": crawler.name,
                "fetched": 0,
                "new":     0,
                "status":  "error",
                "error":   str(e),
            })
            logger.error("[%s] 오류 발생: %s", crawler.name, e, exc_info=True)

    logger.info("=== 전체 크롤링 완료 — 신규 %d건 ===", total_new)
    return {
        "total_new":     total_new,
        "total_fetched": total_fetched,
        "details":       details,
    }
