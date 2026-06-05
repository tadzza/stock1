# crawler/base_crawler.py
import time
import logging
import requests
from abc import ABC, abstractmethod
from config import HEADERS, REQUEST_DELAY, REQUEST_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):

    name: str = "BaseCrawler"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str, **kwargs):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(
                    url, timeout=REQUEST_TIMEOUT, **kwargs
                )
                resp.raise_for_status()
                time.sleep(REQUEST_DELAY)
                return resp
            except requests.RequestException as e:
                logger.warning("[%s] 요청 실패 (시도 %d/%d) %s — %s",
                               self.name, attempt, MAX_RETRIES, url, e)
                if attempt < MAX_RETRIES:
                    time.sleep(REQUEST_DELAY * attempt * 2)
        return None

    @abstractmethod
    def fetch(self) -> list:
        ...

    @staticmethod
    def _normalize(record: dict) -> dict:
        defaults = {
            "stock_name":   "",
            "title":        "",
            "firm":         "",
            "pub_date":     "",
            "download_url": "",
            "opinion":      "",
            "target_price": "",
            "analyst":      "",
            "category":     "기업분석",
        }
        defaults.update(record)
        return {k: (v.strip() if isinstance(v, str) else v)
                for k, v in defaults.items()}
