"""公考招考监控 - 爬虫入口。

用法：
    python run.py            # 抓取全部来源
    python run.py --demo     # 不联网，写入示例数据（用于本地预览网页）

环境依赖：
    pip install -r requirements.txt
    python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

# 让 `python run.py` 也能直接 import crawler 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.sources import SOURCES  # noqa: E402
from crawler.scraper import crawl_all  # noqa: E402
from crawler.dedupe import load_existing, merge, save  # noqa: E402

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


DEMO_DATA = [
    {
        "category": "国考",
        "source": "国家公务员局-国考专题",
        "title": "中央机关及其直属机构2026年度考试录用公务员公告",
        "publish_date": "2026-10-14",
        "registration_start": "2026-10-15",
        "registration_end": "2026-10-24",
        "exam_date": "2026-11-30",
        "url": "http://bm.scs.gov.cn/",
    },
    {
        "category": "中央遴选",
        "source": "国家公务员局-中央机关公开遴选",
        "title": "2026年度中央机关公开遴选和公开选调公务员公告",
        "publish_date": "2026-01-08",
        "registration_start": "2026-01-09",
        "registration_end": "2026-01-15",
        "exam_date": "2026-03-01",
        "url": "http://sub.scs.gov.cn/",
    },
    {
        "category": "省考",
        "source": "广东人事考试网",
        "title": "2026年广东省考试录用公务员公告",
        "publish_date": "2026-01-05",
        "registration_start": "2026-01-06",
        "registration_end": "2026-01-12",
        "exam_date": "2026-03-15",
        "url": "http://rsks.gd.gov.cn/",
    },
    {
        "category": "各省选调",
        "source": "山东定向选调",
        "title": "山东省2026年度定向选调应届优秀毕业生公告",
        "publish_date": "2026-11-20",
        "registration_start": "2026-11-21",
        "registration_end": "2026-11-27",
        "exam_date": "2026-12-21",
        "url": "http://www.dtd.shandong.gov.cn/",
    },
]


async def run_crawl() -> None:
    print(f"=== 公考招考监控爬虫启动 {datetime.now():%Y-%m-%d %H:%M:%S} ===")
    print(f"来源数量：{len(SOURCES)}")
    new_items = await crawl_all(SOURCES)

    existing = load_existing()
    merged, newly = merge(new_items, existing)
    save(merged)

    print(f"\n=== 完成 ===")
    print(f"本轮抓取候选：{len(new_items)} 条")
    print(f"新增公告：{len(newly)} 条")
    print(f"累计公告：{len(merged)} 条")
    print(f"数据写入：{DATA_FILE}")


def run_demo() -> None:
    """写入示例数据，便于离线预览网页。"""
    existing = load_existing()
    merged, newly = merge(DEMO_DATA, existing)
    save(merged)
    print(f"已写入示例数据：新增 {len(newly)} 条，累计 {len(merged)} 条 -> {DATA_FILE}")


def main() -> None:
    parser = argparse.ArgumentParser(description="公考招考监控爬虫")
    parser.add_argument(
        "--demo", action="store_true", help="不联网，仅写入示例数据用于预览网页"
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    try:
        asyncio.run(run_crawl())
    except KeyboardInterrupt:
        print("\n已中断。")


if __name__ == "__main__":
    # 若 data.json 不存在，先初始化空结构
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_updated": None, "total": 0, "new_count": 0, "announcements": []}, f, ensure_ascii=False, indent=2)
    main()
