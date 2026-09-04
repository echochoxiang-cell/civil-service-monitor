"""去重与持久化：只保存新公告，新增公告打上 new 标记。

去重依据：公告 url + title 的 md5（短）作为 id。
合并策略：
    - 历史公告 is_new = False
    - 本轮新增且发布日期在最近 RECENT_DAYS 天内 → is_new = True
    - 发布日期 < MIN_PUBLISH_DATE 的条目：新数据不入库，已入库的下次 merge 时删除
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta

from crawler.sources import MIN_PUBLISH_DATE, RECENT_DAYS

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json")


def _make_id(item: dict) -> str:
    base = f"{item.get('url','')}|{item.get('title','')}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:16]


def _is_within_window(date_str: str, cutoff_iso: str) -> bool:
    """发布日期 >= cutoff_iso 视为在展示窗口内。空日期视为在窗口内（不在此处拦截）。"""
    if not date_str:
        return True
    try:
        return datetime.strptime(date_str, "%Y-%m-%d") >= datetime.strptime(cutoff_iso, "%Y-%m-%d")
    except ValueError:
        return True


def _is_recent(date_str: str, days: int = RECENT_DAYS) -> bool:
    """发布日期是否在最近 N 天内（含今天）。空日期或非法格式视为非最近（不打 new 标记）。"""
    if not date_str:
        return False
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False
    cutoff = datetime.now() - timedelta(days=days)
    return d >= cutoff


def load_existing() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("announcements", [])
    except (json.JSONDecodeError, OSError):
        return []


def merge(new_items: list[dict], existing: list[dict]) -> tuple[list[dict], list[dict]]:
    """合并新抓取数据与历史数据。返回 (全部公告, 本轮新增)。

    规则：
      1. 发布日期 < MIN_PUBLISH_DATE 的新条目：不入库
      2. 历史条目中发布日期 < MIN_PUBLISH_DATE 的：从 merged 中剔除（删除）
      3. 本轮新增且发布日期在最近 RECENT_DAYS 天内 → is_new = True
    """
    existing_ids = {x["id"] for x in existing if "id" in x}

    # 历史公告全部取消 new 标记
    for x in existing:
        x["is_new"] = False

    newly_added: list[dict] = []
    for item in new_items:
        item["id"] = _make_id(item)
        # 时间窗：早于 MIN_PUBLISH_DATE 的不入库
        if not _is_within_window(item.get("publish_date", ""), MIN_PUBLISH_DATE):
            continue
        if item["id"] in existing_ids:
            continue
        # is_new 仅当发布日期在最近 RECENT_DAYS 天内
        item["is_new"] = _is_recent(item.get("publish_date", ""))
        item["crawled_at"] = datetime.now().isoformat(timespec="seconds")
        newly_added.append(item)

    # 历史条目中删除早于 MIN_PUBLISH_DATE 的（用户确认：删除而非保留）
    kept_existing = [
        x for x in existing
        if _is_within_window(x.get("publish_date", ""), MIN_PUBLISH_DATE)
    ]
    removed_count = len(existing) - len(kept_existing)
    if removed_count:
        print(f"  [dedupe] 删除 {removed_count} 条早于 {MIN_PUBLISH_DATE} 的历史条目")

    # 新公告置顶
    merged = newly_added + kept_existing
    return merged, newly_added


def save(announcements: list[dict]) -> None:
    payload = {
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "total": len(announcements),
        "new_count": sum(1 for a in announcements if a.get("is_new")),
        "announcements": announcements,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
