# crawler/naver_crawler.py
import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler
from config import MAX_PAGES

logger = logging.getLogger(__name__)

NAVER_COMPANY_URL = (
    "https://finance.naver.com/research/company_list.naver"
    "?&page={page}"
)
NAVER_INDUSTRY_URL = (
    "https://finance.naver.com/research/industry_list.naver"
    "?&page={page}"
)
NAVER_BASE = "https://finance.naver.com"


class NaverCompanyCrawler(BaseCrawler):

    name = "naver_company"

    def fetch(self) -> list:
        reports = []
        for page in range(1, MAX_PAGES + 1):
            url  = NAVER_COMPANY_URL.format(page=page)
            resp = self._get(url)
            if resp is None:
                logger.warning("[%s] 페이지 %d 응답 없음, 중단", self.name, page)
                break

            html  = resp.content.decode("cp949", errors="replace")
            items = self._parse_company_page(html)

            if not items:
                logger.info("[%s] 페이지 %d 데이터 없음", self.name, page)
                break

            reports.extend(items)
            logger.info("[%s] 페이지 %d: %d건 수집", self.name, page, len(items))

        logger.info("[%s] 총 %d건 수집 완료", self.name, len(reports))
        return reports

    def _parse_company_page(self, html: str) -> list:
        soup  = BeautifulSoup(html, "lxml")
        table = soup.select_one("table.type_1")
        if not table:
            return []

        records = []
        for row in table.select("tr"):
            tds = row.select("td")
            if len(tds) < 6:
                continue
            try:
                stock_name   = tds[0].get_text(strip=True)
                title_tag    = tds[1].select_one("a")
                title        = title_tag.get_text(strip=True) if title_tag else ""
                download_url = self._extract_download_url(tds[1])
                opinion      = tds[2].get_text(strip=True)
                target_price = tds[3].get_text(strip=True)
                firm         = tds[4].get_text(strip=True)
                pub_date     = self._parse_date(tds[5].get_text(strip=True))

                if not stock_name or not title or not firm:
                    continue

                records.append(self._normalize({
                    "stock_name":   stock_name,
                    "title":        title,
                    "firm":         firm,
                    "pub_date":     pub_date,
                    "download_url": download_url,
                    "opinion":      opinion,
                    "target_price": target_price,
                    "analyst":      "",
                    "category":     "기업분석",
                }))
            except Exception as e:
                logger.debug("[%s] 행 파싱 오류: %s", self.name, e)
                continue

        return records

    def _extract_download_url(self, td) -> str:
        for a in td.select("a"):
            href = a.get("href", "")
            if href and (".pdf" in href.lower() or "download" in href.lower()):
                return href if href.startswith("http") else NAVER_BASE + href
        a = td.select_one("a")
        if a:
            href = a.get("href", "")
            if href:
                return href if href.startswith("http") else NAVER_BASE + href
        return ""

    @staticmethod
    def _parse_date(raw: str) -> str:
        raw = raw.strip()
        m = re.match(r"^(\d{2})\.(\d{2})\.(\d{2})$", raw)
        if m:
            yy, mm, dd = m.groups()
            return f"20{yy}-{mm}-{dd}"
        m = re.match(r"^(\d{4})\.(\d{2})\.(\d{2})$", raw)
        if m:
            yyyy, mm, dd = m.groups()
            return f"{yyyy}-{mm}-{dd}"
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw)
        if m:
            return raw
        return datetime.now().strftime("%Y-%m-%d")


class NaverIndustryCrawler(BaseCrawler):

    name = "naver_industry"

    def __init__(self):
        super().__init__()
        self._base = NaverCompanyCrawler()

    def fetch(self) -> list:
        reports = []
        for page in range(1, MAX_PAGES + 1):
            url  = NAVER_INDUSTRY_URL.format(page=page)
            resp = self._get(url)
            if resp is None:
                break

            html  = resp.content.decode("cp949", errors="replace")
            items = self._parse_industry_page(html)
            if not items:
                break

            reports.extend(items)
            logger.info("[%s] 페이지 %d: %d건 수집", self.name, page, len(items))

        logger.info("[%s] 총 %d건 수집 완료", self.name, len(reports))
        return reports

    def _parse_industry_page(self, html: str) -> list:
        soup  = BeautifulSoup(html, "lxml")
        table = soup.select_one("table.type_1")
        if not table:
            return []

        records = []
        for row in table.select("tr"):
            tds = row.select("td")
            if len(tds) < 4:
                continue
            try:
                industry  = tds[0].get_text(strip=True)
                title_tag = tds[1].select_one("a")
                title     = title_tag.get_text(strip=True) if title_tag else ""
                dl_url    = self._base._extract_download_url(tds[1])
                firm      = tds[2].get_text(strip=True)
                pub_date  = NaverCompanyCrawler._parse_date(
                    tds[3].get_text(strip=True)
                )
                if not industry or not title or not firm:
                    continue
                records.append(self._base._normalize({
                    "stock_name": industry,
                    "title":      title,
                    "firm":       firm,
                    "pub_date":   pub_date,
                    "download_url": dl_url,
                    "category":   "산업분석",
                }))
            except Exception as e:
                logger.debug("[%s] 행 파싱 오류: %s", self.name, e)
        return records
