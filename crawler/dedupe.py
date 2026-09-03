"""去重与持久化：只保存新公告，新增公告打上 new 标记。

去重依据：公告 url + title 的 md5（短）作为 id。
合并策略：保留历史全部公告，每轮抓取后：
    - 历史公告 is_new = False
    - 本轮新增公告 is_new = True
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json")


def _make_id(item: dict) -> str:
    base = f"{item.get('url','')}|{item.get('title','')}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:16]


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
    """合并新抓取数据与历史数据。返回 (全部公告, 本轮新增)。"""
    existing_ids = {x["id"] for x in existing if "id" in x}

    # 历史公告全部取消 new 标记
    for x in existing:
        x["is_new"] = False

    newly_added: list[dict] = []
    for item in new_items:
        item["id"] = _make_id(item)
        if item["id"] in existing_ids:
            continue
        item["is_new"] = True
        item["crawled_at"] = datetime.now().isoformat(timespec="seconds")
        newly_added.append(item)

    # 新公告置顶
    merged = newly_added + existing
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
