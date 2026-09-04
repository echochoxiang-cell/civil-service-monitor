"""基于 Playwright 的通用招考公告抓取器。

设计思路：
    1. 访问来源列表页，提取所有 <a> 链接；
    2. 按关键词过滤出"候选公告"链接；
    3. 从链接所在父级行文本中解析发布日期；
    4. 对每个来源最多进入 detail_limit 个详情页，友好延时，
       从正文按关键词邻近原则解析 报名开始/截止、笔试时间；
    5. 全程 try/except，单页失败不影响整体。

友好访问：页面间随机延时 2~4 秒，列表页加载后等待渲染。
"""

from __future__ import annotations

import asyncio
import random
import re
from datetime import datetime, timedelta
from typing import Iterable
from urllib.parse import urljoin

from crawler.sources import NEGATIVE_KW, POSITIVE_EXTRA, RECENT_DAYS

# 日期匹配：2026-09-01 / 2026年9月1日 / 2026.09.01
DATE_RE = re.compile(
    r"(20\d{2})\s*[-年./]\s*(\d{1,2})\s*[-月./]\s*(\d{1,2})"
)

# 发布日期关键词（按优先级排序，匹配行命中任一即把该行日期作为发布日期）
PUBLISH_DATE_KEYWORDS = [
    "发布时间", "发布日期", "发文日期", "印发日期", "公布日期",
    "发布", "发文", "印发", "公布",
]


def parse_date(text: str | None) -> str | None:
    """从文本中提取第一个合法日期，返回 YYYY-MM-DD。"""
    if not text:
        return None
    m = DATE_RE.search(text)
    if not m:
        return None
    try:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1 <= mo <= 12 and 1 <= d <= 31):
            return None
        return f"{y:04d}-{mo:02d}-{d:02d}"
    except ValueError:
        return None


def _find_dates_near(text: str) -> tuple[str | None, str | None, str | None]:
    """按行扫描文本，用关键词邻近原则解析报名开始/截止/笔试时间。"""
    reg_start = reg_end = exam_date = None
    # 把常见标点切成行
    lines = re.split(r"[。\n；;]", text or "")
    for line in lines:
        if not line.strip():
            continue
        d = parse_date(line)
        if not d:
            continue
        line_low = line
        if ("报名" in line_low and ("开始" in line_low or "起" in line_low)) \
                or ("报名时间" in line_low and "截止" not in line_low):
            reg_start = reg_start or d
        if ("截止" in line_low or "结束" in line_low or "至" in line_low) and "报名" in line_low:
            reg_end = reg_end or d
        if "笔试" in line_low:
            exam_date = exam_date or d
        # 兜底：含"时间"且含日期的行，优先记到笔试
        if "时间" in line_low and not exam_date and "笔试" in line_low:
            exam_date = d
    return reg_start, reg_end, exam_date


def _parse_publish_date(text: str | None) -> str | None:
    """解析发布日期：优先匹配"发布时间/发布日期/发文日期"等关键词所在行的日期，
    找不到则退化到文本中第一个日期（兜底）。
    """
    if not text:
        return None
    lines = re.split(r"[。\n；;]", text)
    # 第一轮：命中发布日期关键词的行
    for line in lines:
        if not line.strip():
            continue
        if any(k in line for k in PUBLISH_DATE_KEYWORDS):
            d = parse_date(line)
            if d:
                return d
    # 第二轮：兜底取第一个日期
    return parse_date(text)


def _is_noise(text: str) -> bool:
    """负向过滤：文本命中任一负向关键词即判为噪声。"""
    if not text:
        return False
    return any(k in text for k in NEGATIVE_KW)


def _has_positive(text: str, source_keywords: list[str]) -> bool:
    """正向过滤：文本命中（来源关键词 ∪ 全局正向词）任一即通过。"""
    if not text:
        return False
    pos = set(source_keywords) | set(POSITIVE_EXTRA)
    return any(k in text for k in pos)


def _within_recent_days(date_str: str | None, days: int = RECENT_DAYS) -> bool:
    """判断发布日期是否在最近 N 天内（含今天）。
    返回 False 表示早于窗口或日期非法——应跳过。
    """
    if not date_str:
        return True  # 解析不到日期时不在此处拦截，留给详情页阶段处理
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return True
    cutoff = datetime.now() - timedelta(days=days)
    return d >= cutoff


def _resolve(url: str, href: str | None) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.startswith(("javascript:", "#", "mailto:")):
        return None
    return urljoin(url, href)


async def _extract_links(page, source: dict) -> list[dict]:
    """提取列表页候选公告链接。

    过滤规则（全局应用于所有来源）：
      1. 正向：链接文本命中（来源 keywords ∪ POSITIVE_EXTRA）任一
      2. 负向：链接文本命中 NEGATIVE_KW 任一即丢弃（搬迁/关闭/成绩/列表汇总页等）
      3. 时间窗：解析到发布日期且早于最近 RECENT_DAYS 天的，不进候选（节省详情页访问）
    """
    candidates: list[dict] = []
    seen: set[str] = set()
    anchors = await page.query_selector_all("a")
    for a in anchors:
        try:
            text = (await a.inner_text()).strip()
            href = await a.get_attribute("href")
        except Exception:
            continue
        if not text or len(text) > 80:
            # 标题通常不会过长也不会为空
            continue
        # 负向过滤：搬迁/关闭/成绩/列表汇总页等噪声直接丢弃
        if _is_noise(text):
            continue
        # 正向过滤：必须命中（来源关键词 ∪ 全局正向词）至少一个
        if not _has_positive(text, source["keywords"]):
            continue
        url = _resolve(source["url"], href)
        if not url or url in seen:
            continue
        seen.add(url)

        # 尝试从父级行文本中解析发布日期
        pub_date = None
        try:
            parent = await a.evaluate_handle(
                "el => el.closest('tr,li,dd,div') ? el.closest('tr,li,dd,div').innerText : ''"
            )
            parent_text = await parent.json_value()
            pub_date = _parse_publish_date(parent_text)
        except Exception:
            pass

        # 时间窗：解析到日期且早于最近 RECENT_DAYS 天的，不进候选（节省详情页访问）
        if not _within_recent_days(pub_date):
            continue

        candidates.append({
            "title": text,
            "url": url,
            "publish_date": pub_date,
        })
    return candidates


async def _extract_detail(page) -> str:
    """获取详情页正文文本（限定长度，避免内存爆炸）。"""
    try:
        body = await page.query_selector("body")
        if not body:
            return ""
        text = await body.inner_text()
        return text[:8000]
    except Exception:
        return ""


async def scrape_source(context, source: dict) -> list[dict]:
    """抓取单个来源，返回公告列表。"""
    results: list[dict] = []
    page = await context.new_page()
    page.set_default_timeout(30000)
    try:
        try:
            await page.goto(source["url"], wait_until="domcontentloaded")
        except Exception as e:
            print(f"  [warn] 列表页打开失败 {source['name']}: {e}")
            return results
        await page.wait_for_timeout(2500)  # 等待动态渲染

        candidates = await _extract_links(page, source)
        print(f"  候选公告 {len(candidates)} 条")

        limit = min(source.get("detail_limit", 6), len(candidates))
        for item in candidates[:limit]:
            await asyncio.sleep(random.uniform(2.0, 4.0))  # 友好延时
            detail = await context.new_page()
            try:
                try:
                    await detail.goto(item["url"], wait_until="domcontentloaded")
                except Exception as e:
                    print(f"  [warn] 详情页失败 {item['url']}: {e}")
                    continue
                await detail.wait_for_timeout(2000)
                body = await _extract_detail(detail)

                # 详情页正文二次过滤：负向词命中则丢弃，正向词必须至少命中一个
                if _is_noise(body):
                    print(f"  [skip] 详情页命中负向词，丢弃：{item['title'][:30]}")
                    continue
                if not _has_positive(body, source["keywords"]):
                    print(f"  [skip] 详情页未命中正向词，丢弃：{item['title'][:30]}")
                    continue

                reg_start, reg_end, exam_date = _find_dates_near(body)
                # 二次解析发布日期：优先用"发布时间/发文日期"等关键词邻近的日期
                pub_date = item["publish_date"] or _parse_publish_date(body[:3000])

                results.append({
                    "category": source["category"],
                    "source": source["name"],
                    "title": item["title"],
                    "publish_date": pub_date or "",
                    "registration_start": reg_start or "",
                    "registration_end": reg_end or "",
                    "exam_date": exam_date or "",
                    "url": item["url"],
                })
            finally:
                await detail.close()

    finally:
        await page.close()
    return results


async def crawl_all(sources: Iterable[dict]) -> list[dict]:
    """抓取全部来源，来源之间加延时。"""
    from playwright.async_api import async_playwright

    all_items: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )
        for src in sources:
            print(f"[{datetime.now():%H:%M:%S}] 抓取 {src['name']} ({src['category']})")
            try:
                items = await scrape_source(context, src)
                all_items.extend(items)
                print(f"  -> 采集 {len(items)} 条")
            except Exception as e:
                print(f"  [error] {src['name']}: {e}")
            await asyncio.sleep(random.uniform(3.0, 5.0))  # 来源间延时
        await browser.close()
    return all_items
