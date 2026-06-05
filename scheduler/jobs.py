# scheduler/jobs.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from config import SCHEDULER_HOUR, SCHEDULER_MINUTE

logger = logging.getLogger(__name__)


def _crawl_job():
    from crawler.manager import run_all_crawlers
    from briefing.generator import generate_daily_briefing

    logger.info("[ SCHEDULER ] 정기 크롤링 시작")
    result = run_all_crawlers()
    logger.info("[ SCHEDULER ] 크롤링 완료: 신규 %d건", result["total_new"])

    logger.info("[ SCHEDULER ] 브리핑 생성 시작")
    generate_daily_briefing()
    logger.info("[ SCHEDULER ] 브리핑 생성 완료")


def _job_listener(event):
    if event.exception:
        logger.error("스케줄 작업 오류: %s", event.exception)
    else:
        logger.info("스케줄 작업 정상 완료 (job_id=%s)", event.job_id)


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(
        timezone="Asia/Seoul",
        job_defaults={"misfire_grace_time": 3600}
    )

    scheduler.add_job(
        func    = _crawl_job,
        trigger = CronTrigger(
            hour     = SCHEDULER_HOUR,
            minute   = SCHEDULER_MINUTE,
            timezone = "Asia/Seoul"
        ),
        id               = "daily_crawl",
        name             = "일일 리서치 레포트 수집",
        replace_existing = True,
    )

    scheduler.add_listener(
        _job_listener,
        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
    )
    return scheduler
