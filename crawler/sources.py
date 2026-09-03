"""招考信息来源配置。

每个来源包含：
    name        : 来源名称（用于展示与日志）
    category    : 考试类别（国考 / 省考 / 中央遴选 / 各省选调）
    url         : 公告列表页 URL
    keywords    : 链接文本需包含的关键词（任一命中即作为候选公告）
    detail_limit: 该来源最多进入的详情页数量（友好访问，避免高频请求）

注意：各省人事考试网 / 省委组织部页面结构会随年份变化，
      如遇选择器失效，仅需调整这里的 url 与 keywords 即可，
      爬虫主体逻辑无需改动。
"""

SOURCES = [
    # ---------------- 国考 ----------------
    {
        "name": "国家公务员局-国考专题",
        "category": "国考",
        "url": "http://bm.scs.gov.cn/",
        "keywords": ["公告", "招录", "职位", "报名", "公务员"],
        "detail_limit": 6,
    },
    {
        "name": "国家公务员局-考试录用",
        "category": "国考",
        "url": "https://www.scs.gov.cn/",
        "keywords": ["公告", "招录", "报名", "职位表"],
        "detail_limit": 4,
    },

    # ---------------- 中央遴选选调 ----------------
    {
        "name": "国家公务员局-中央机关公开遴选",
        "category": "中央遴选",
        "url": "http://sub.scs.gov.cn/",
        "keywords": ["遴选", "选调", "公告", "职位"],
        "detail_limit": 6,
    },
    {
        "name": "国家公务员局-公开选调",
        "category": "中央遴选",
        "url": "https://www.scs.gov.cn/",
        "keywords": ["遴选", "选调", "公告"],
        "detail_limit": 4,
    },

    # ---------------- 省考（各省人事考试网） ----------------
    {
        "name": "北京人事考试",
        "category": "省考",
        "url": "http://www.bjpta.cn/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "广东人事考试网",
        "category": "省考",
        "url": "http://rsks.gd.gov.cn/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "浙江人事考试网",
        "category": "省考",
        "url": "https://www.zjks.com/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "江苏人事考试",
        "category": "省考",
        "url": "https://jshrss.jiangsu.gov.cn/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "山东人事考试",
        "category": "省考",
        "url": "http://hrss.shandong.gov.cn/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "四川人事考试网",
        "category": "省考",
        "url": "http://www.scpta.com.cn/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "河南人事考试",
        "category": "省考",
        "url": "http://www.hnrsks.com/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "湖北人事考试网",
        "category": "省考",
        "url": "http://www.hbsrsksy.cn/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },
    {
        "name": "河北人事考试网",
        "category": "省考",
        "url": "https://www.hebpta.com.cn/",
        "keywords": ["公务员", "公告", "招录", "报名", "考试"],
        "detail_limit": 6,
    },

    # ---------------- 各省定向选调 ----------------
    {
        "name": "北京人社-选调生",
        "category": "各省选调",
        "url": "http://rsj.beijing.gov.cn/",
        "keywords": ["选调", "定向", "公告", "报名"],
        "detail_limit": 6,
    },
    {
        "name": "山东定向选调",
        "category": "各省选调",
        "url": "http://www.dtd.shandong.gov.cn/",
        "keywords": ["选调", "定向", "公告", "报名"],
        "detail_limit": 6,
    },
    {
        "name": "四川选调生",
        "category": "各省选调",
        "url": "http://www.scpta.com.cn/",
        "keywords": ["选调", "定向", "公告", "报名"],
        "detail_limit": 6,
    },
    {
        "name": "浙江选调生",
        "category": "各省选调",
        "url": "https://www.zjks.com/",
        "keywords": ["选调", "定向", "公告", "报名"],
        "detail_limit": 6,
    },
]
