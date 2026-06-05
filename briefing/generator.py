# briefing/generator.py
import os
import logging
from datetime import datetime
from models.database import get_today_reports
from config import BRIEFING_DIR

logger = logging.getLogger(__name__)

os.makedirs(BRIEFING_DIR, exist_ok=True)


def generate_daily_briefing(date_str: str = None) -> str:
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    reports  = get_today_reports()
    html     = _render_briefing_html(date_str, reports)
    filename = f"briefing_{date_str}.html"
    filepath = os.path.join(BRIEFING_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("브리핑 생성 완료: %s (%d건)", filepath, len(reports))
    return filepath


def _render_briefing_html(date_str: str, reports: list) -> str:
    grouped = {}
    for r in reports:
        grouped.setdefault(r["firm"], []).append(r)

    firm_sections = ""
    for firm, items in sorted(grouped.items()):
        rows = ""
        for r in items:
            opinion_badge = _opinion_badge(r.get("opinion", ""))
            link_html = (
                f'<a href="{r["download_url"]}" target="_blank" '
                f'class="download-btn">📄 원문</a>'
                if r.get("download_url") else "—"
            )
            rows += f"""
            <tr>
                <td class="stock">{r['stock_name']}</td>
                <td class="title">{r['title']}</td>
                <td>{opinion_badge}</td>
                <td class="price">{r.get('target_price') or '—'}</td>
                <td>{link_html}</td>
            </tr>"""
        firm_sections += f"""
        <section class="firm-section">
            <h3>🏢 {firm} <span class="count">{len(items)}건</span></h3>
            <table>
                <thead>
                    <tr>
                        <th>종목명</th><th>레포트 제목</th>
                        <th>투자의견</th><th>목표주가</th><th>원문</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </section>"""

    total  = len(reports)
    n_firm = len(grouped)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 일일 리서치 브리핑 — {date_str}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
               background: #f0f4f8; color: #2d3748; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px; }}
        header {{ background: linear-gradient(135deg, #1a365d, #2b6cb0);
                  color: white; padding: 32px; border-radius: 12px;
                  margin-bottom: 24px; }}
        header h1 {{ font-size: 1.8rem; margin-bottom: 8px; }}
        header p {{ opacity: 0.85; font-size: 0.95rem; }}
        .stats-bar {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
        .stat-card {{ background: white; border-radius: 10px; padding: 16px 24px;
                      box-shadow: 0 1px 4px rgba(0,0,0,.1); flex: 1;
                      min-width: 140px; text-align: center; }}
        .stat-card .number {{ font-size: 2rem; font-weight: 700; color: #2b6cb0; }}
        .stat-card .label  {{ font-size: 0.8rem; color: #718096; }}
        .firm-section {{ background: white; border-radius: 10px; padding: 20px;
                          margin-bottom: 20px;
                          box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
        .firm-section h3 {{ font-size: 1.1rem; color: #1a365d;
                            border-bottom: 2px solid #e2e8f0;
                            padding-bottom: 10px; margin-bottom: 14px; }}
        .count {{ background: #ebf8ff; color: #2b6cb0; font-size: 0.75rem;
                  padding: 2px 8px; border-radius: 12px;
                  font-weight: 600; vertical-align: middle; margin-left: 8px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
        th {{ background: #f7fafc; text-align: left; padding: 8px 10px;
              color: #4a5568; font-weight: 600; border-bottom: 1px solid #e2e8f0; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #f0f4f8; vertical-align: middle; }}
        tr:last-child td {{ border-bottom: none; }}
        td.stock {{ font-weight: 600; color: #1a365d; white-space: nowrap; }}
        td.title {{ max-width: 320px; }}
        td.price {{ white-space: nowrap; color: #e53e3e; font-weight: 600; }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 600; white-space: nowrap; }}
        .badge-buy     {{ background: #fed7d7; color: #c53030; }}
        .badge-hold    {{ background: #fefcbf; color: #744210; }}
        .badge-neutral {{ background: #e2e8f0; color: #4a5568; }}
        .download-btn {{ background: #2b6cb0; color: white; padding: 4px 10px;
                         border-radius: 6px; text-decoration: none; font-size: 0.8rem; }}
        .download-btn:hover {{ background: #2c5282; }}
        footer {{ text-align: center; color: #a0aec0; font-size: 0.8rem;
                  margin-top: 32px; padding: 16px; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>📊 일일 리서치 레포트 브리핑</h1>
        <p>{date_str} 기준 · 총 {total}건 · {n_firm}개 증권사</p>
    </header>
    <div class="stats-bar">
        <div class="stat-card">
            <div class="number">{total}</div>
            <div class="label">총 레포트 수</div>
        </div>
        <div class="stat-card">
            <div class="number">{n_firm}</div>
            <div class="label">증권사 수</div>
        </div>
        <div class="stat-card">
            <div class="number">{len([r for r in reports if '매수' in (r.get('opinion') or '')])}</div>
            <div class="label">매수 의견</div>
        </div>
    </div>
    {firm_sections if firm_sections else
     '<p style="text-align:center;color:#a0aec0;padding:40px;">오늘 수집된 레포트가 없습니다.</p>'}
    <footer>
        자동 생성 — {datetime.now().strftime('%Y-%m-%d %H:%M')} |
        본 자료는 투자 권유가 아닙니다.
    </footer>
</div>
</body>
</html>"""


def _opinion_badge(opinion: str) -> str:
    if not opinion:
        return '<span class="badge badge-neutral">—</span>'
    op = opinion.upper()
    if any(k in op for k in ["매수", "BUY", "강력매수"]):
        return f'<span class="badge badge-buy">{opinion}</span>'
    if any(k in op for k in ["중립", "HOLD", "NEUTRAL"]):
        return f'<span class="badge badge-hold">{opinion}</span>'
    return f'<span class="badge badge-neutral">{opinion}</span>'
