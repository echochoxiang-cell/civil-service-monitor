# 公考招考监控

每日自动抓取国考、省考、中央遴选、各省定向选调官方公告，去重后输出 `data.json`，并通过简洁网页按考试类别分组展示，新公告高亮。GitHub Actions 每天北京时间 08:00 自动抓取并部署到 GitHub Pages。

## 项目结构

```
monitoring_test/
├── crawler/
│   ├── __init__.py      # 包入口
│   ├── sources.py       # 抓取来源配置（URL、关键词、类别）
│   ├── scraper.py       # Playwright 抓取逻辑 + 日期解析
│   └── dedupe.py        # 去重 + 持久化（new 标记）
├── data.json            # 抓取结果（网页读取的数据源）
├── index.html           # 网页（Tailwind，读取 data.json）
├── run.py               # 爬虫入口（python run.py）
├── requirements.txt     # Python 依赖
└── .github/workflows/
    └── daily-crawl.yml  # 每日定时抓取 + Pages 部署
```

## 抓取字段

| 字段 | 说明 |
| --- | --- |
| category | 考试类别：国考 / 省考 / 中央遴选 / 各省选调 |
| source | 来源网站名称 |
| title | 公告标题 |
| publish_date | 发布日期 |
| registration_start | 报名开始 |
| registration_end | 报名截止 |
| exam_date | 笔试时间 |
| url | 公告原文链接 |
| is_new | 是否本轮新增 |

## 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt
python -m playwright install chromium

# 2. 仅写入示例数据（离线预览网页，不联网）
python run.py --demo

# 3. 正式抓取（联网，访问各官网）
python run.py

# 4. 本地预览网页（任选其一）
python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

> 说明：爬虫对所有来源采用通用抓取策略（提取 `<a>` 链接 + 关键词过滤 + 父级行解析日期），页面结构会随年份变化。如某站点抓取失败，调整 `crawler/sources.py` 中对应来源的 `url` 与 `keywords` 即可，主体逻辑无需改动。请求间设有 2~5 秒随机延时，友好访问官网。

## 部署到 GitHub Pages（步骤）

### 1. 创建仓库并推送代码
```bash
git init
git add .
git commit -m "init: 公考招考监控项目"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

### 2. 开启 GitHub Pages（Source 选 GitHub Actions）
本仓库使用 GitHub 官方部署方式（`actions/deploy-pages`），无需创建 `gh-pages` 分支：
1. 进入仓库 **Settings → Pages**；
2. **Build and deployment → Source** 选择 `GitHub Actions`；
3. 保存即可（无需选分支，Workflow 会自动部署）。

### 3. 配置定时任务
仓库已自带 `.github/workflows/daily-crawl.yml`：
- `cron: '0 0 * * *'`（UTC 00:00 = 北京时间 08:00）每天自动运行；
- 也可在 **Actions** 页面手动触发（`workflow_dispatch`）；
- 流程：抓取 → 提交 data.json 到 main → 仅打包 `index.html` + `data.json` 部署到 Pages。

> 注意：GitHub Actions 的 cron 在高峰期可能延迟几分钟到几十分钟，属正常现象。

### 4. 首次运行并验证
1. 进入仓库 **Actions** 标签页，左侧选 `Daily Crawl and Deploy`；
2. 点 `Enable workflows`（首次需启用），再点右上角 `Run workflow` 手动触发一次；
3. 等待运行成功（绿色），其中 `deploy` 步骤会输出 Pages 访问地址；
4. 访问 `https://<你的用户名>.github.io/<仓库名>/` 即可看到网页。

> 若仓库命名为 `<你的用户名>.github.io`，则访问 `https://<你的用户名>.github.io/`。

## 自定义来源

编辑 [crawler/sources.py](crawler/sources.py)，按以下结构新增来源即可：

```python
{
    "name": "来源名称",
    "category": "国考",           # 国考 / 省考 / 中央遴选 / 各省选调
    "url": "http://xxx.gov.cn/",
    "keywords": ["公告", "招录"],   # 链接文本需命中的关键词
    "detail_limit": 6,            # 最多进入的详情页数量
}
```

## 技术栈
- 爬虫：Python + Playwright（headless Chromium）
- 前端：原生 HTML + Tailwind CSS（CDN）
- 部署：GitHub Actions + GitHub Pages
