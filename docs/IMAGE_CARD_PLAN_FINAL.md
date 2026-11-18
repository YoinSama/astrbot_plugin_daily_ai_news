# 图片卡片功能 · 最终开发方案（RSS → HTML → PNG → QQ 消息）

> 状态：**方案稿，尚未修改插件代码**。产物写在 `docs/`，`main.py` / `_conf_schema.json` / `metadata.yaml` / `README.md` 均未改动。
> 此前 `IMAGE_CARD_PLAN.md` 含 T2I 方案，已废弃；本版为最终敲定的纯本地链路。
>
> **条数说明（重要）**：卡片里的新闻条数**不写死**，完全由每次从 RSS `content:encoded` 解析出的 `<li>` 数量决定。
> 文中出现的「29 条 / 720×1380」只是 2026-11-18 这一期的**实测样例值**，用于说明渲染效果，不是代码里的常量；
> 换成任何一期（比如 20 条或 40 条）都会按实际解析结果渲染，顶部计数与截图高度同步自适应。

## 0. 已实测确认的前提

| 事项 | 结论 |
| --- | --- |
| 数据源 | 插件现有 `RSS_URL = https://daily.juya.uk/rss.xml`，取 `channel` 下第一个 item 即最新一期（实测 `2026-11-18`） |
| 条目位置 | 首条 item 的 `content:encoded` 里，`<h2 id="s1">概览</h2>` 之后的一组 `<ul><li>` 就是整期列表，实测 **29 条** |
| 不用 LLM | 概览 li 的标题已是完整新闻标题，直接解析即可，无需调用大模型总结 |
| 渲染方式 | HTML/CSS 模板 + 无头浏览器截图，实测本地 Edge 可出 720×1380 PNG，中文与排版正常 |
| 发送接口 | 本地 AstrBot v4.28.1：`MessageChain().file_image(path)` 加本地图；`context.send_message(umo, chain)` 推送 |

验证脚本与产物（`previews/` 下，已被 `.gitignore` 忽略）：
`gen_from_rss.py`（RSS 解析）、`gen_from_rss_card.py`（模板填充）、`issue_from_rss.html`（模板）、
`issue_from_rss_{light,dark}.png`（明暗成品）。

## 1. 最终链路

```
aiohttp GET rss.xml
  → 取 channel 第一个 item（日期 title、原文 link）
  → 解析 content:encoded 概览区的 <li> → N 条 {序号, 标题}（N = 实际解析出的 li 数，不固定）
  → 选主题（light / dark / 按时段 auto）
  → 填 HTML 模板（CSS 变量切主题，无背景图、无 emoji 依赖）
  → 无头浏览器截图 → PNG（落在数据目录 generated/）
  → MessageChain().file_image(png) → context.send_message(umo, chain)
  → 成功则记日期/链接去重；失败降级现有纯文本
```

## 2. 模块设计

新增包 `image_card/`：

```python
# rss_source.py
def parse_overview(item: dict) -> list[dict]:
    """从首条 item 的 content:encoded 提取概览 li。
    返回 [{index:int, title:str}]，与 previews/gen_from_rss.py 同逻辑：
    截到 <h2 id="s1">概览</h2> 之后，逐个 <li> 去 <a>/<code>/其余标签，html.unescape。"""

# renderer.py
async def render(items, date, link, theme, out_path) -> str:
    """读 templates/card.html → 替换占位符 → 写临时 html →
    调用无头浏览器截图到 out_path → 返回路径。"""

# themes.py
def resolve_theme(now, mode, light_start, dark_start) -> str:
    """auto 时按本地时间段判定，支持夜间跨午夜；否则返回锁定值。"""

# screenshot.py
async def screenshot(html_path, png_path, width=720, height=0) -> bool:
    """封装浏览器调用；height=0 时按条目数估算或截图后自动裁底部空白。"""
```

`main.py` 只增加：配置读取、`/ainews_card` 手动指令、`_do_push()` 里按开关分流；原纯文本链路保留。

## 3. RSS 解析规则（照搬已验证脚本）

1. 复用现有 `_fetch_rss_latest()` 拿到的 `item`（已含 `title` / `link` / `content`）。
2. 注意：现有函数把 `content:encoded` 清洗成纯文本了，解析 li 需要**保留原始 XML 文本**。
   → 在 `_fetch_rss_latest()` 里同时返回 `encoded_raw`（`item.findtext(content:encoded)`，不清洗），
     或新增 `_fetch_issue_raw()` 专供卡片用，避免影响原总结链路。
3. 取 `encoded_raw.split('<h2 id="s1">概览</h2>', 1)[1]`。
4. 正则 `<li>(.*?)</li>` 逐个提取；去 `<a…>…</a>`（↗）、`<code>…</code>`（#N）、其余标签；
   `html.unescape` + 合并空白。
5. 每条写入 `{index: 序号, title: 标题}`，页脚用 item 的 `link`。

## 4. 模板（`templates/card.html`）

以 `previews/issue_from_rss.html` 为基准，占位符：

| 占位符 | 内容 |
| --- | --- |
| `{{DATE}}` | item 的 title，如 `2026-11-18` |
| `{{COUNT}}` | 条目数，取 `len(items)`（本次实测为 29，非固定值） |
| `{{LINK}}` | item 的 link |
| `{{ROWS}}` | 循环生成的 `<div class="item"><div class="num">NN</div><div class="t">标题</div></div>` |

明暗切换：body 加 `.light` / `.dark`，由 CSS 变量控制 `--bg --fg --ac --num --foot --ff`。
沿用已确认样式：顶部品牌条、大标题、副标题、一条细分隔线、编号列表、深色页脚；**不含背景色块**。

## 5. 截图实现

首选本机 Edge（用户环境已验证）：

```bash
msedge.exe --headless=new --disable-gpu --hide-scrollbars \
  --user-data-dir=<临时目录> --force-device-scale-factor=1 \
  --window-size=720,<按条目数计算> \
  --screenshot=<out.png> "file://<html>?view=<theme>"
```

- 高度按 `len(items)` 动态计算（公式随条目数线性增长；实测 29 条 → 1380 只是样例）；
  宁可略高，底部留白可接受，**不能裁掉条目或页脚**。条目数变化时公式自动适配。
- 每次用独立 `--user-data-dir`，避免与已开的 Edge 冲突；用完清理。
- 运行时输出到 `StarTools.get_data_dir()` 下的 `generated/`，文件名 `ainews-{date}-{theme}.png`。
- 部署机若无 Edge：改用 Playwright（`pip install playwright && playwright install chromium`）
  或 Pillow 绘制作为备选——这是落地前需确认的一项。

## 6. 发送与降级

```python
from astrbot.api.message_components import Image  # 备用：event 直发
chain = MessageChain().file_image(str(png_path))
await self.context.send_message(umo, chain)
```

- 定时任务复用现有 `_get_all_targets()` 的 umo 集合，逐个发送，统计成功数。
- 仅当至少一个目标成功才把日期/链接写入 `sent_news.json`（沿用现有去重，避免重复推图）。
- 降级顺序：截图失败 → 重试一次 → 仍失败则发现有纯文本总结；`enable_ai_summary=false` 时不影响卡片。
- 手动指令 `/ainews_card` 即时出图并回给当前会话。

## 7. 配置项（`_conf_schema.json` 新增）

| 配置项 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `enable_image_card` | bool | `false` | 是否启用图片卡片推送 |
| `card_theme_mode` | string | `auto` | `auto` / `light` / `dark` |
| `card_light_start` | string | `07:00` | 明亮时段起点 |
| `card_dark_start` | string | `19:00` | 暗黑时段起点 |
| `card_browser_path` | string | 空 | Edge/Chromium 可执行文件；留空自动探测 |
| `card_send_mode` | string | `image_only` | `image_only` / `image_and_text` |

时间段判定沿用旧方案伪代码（支持跨午夜）；可保留原晚间深色、白天明亮的直觉。

## 8. 新增文件结构

```
image_card/
  __init__.py
  rss_source.py      # 从 content:encoded 提取概览 li
  renderer.py        # 模板填充
  screenshot.py      # 无头浏览器截图
  themes.py          # 主题判定
templates/
  card.html          # 明暗共用的单一模板
generated/           # 运行时 PNG（加入 .gitignore）
docs/IMAGE_CARD_PLAN_FINAL.md
```

已忽略：`previews/`、`generated/`、`image_cache/`、`*.png` 等。

## 9. 分阶段实施

- **阶段 A**：`image_card/` 四个模块 + 模板；用现有 RSS 缓存跑出 PNG，不接 `main.py`。
- **阶段 B**：`main.py` 接线——开关、`/ainews_card`、定时分流、去重与降级。
- **阶段 C**：配置面板、README/CHANGELOG、实机 QQ 发送验证（清晰度、成功率、时段切换）。

## 10. 风险与待确认

1. 部署机是否有 Edge/Chromium？没有则选 Playwright 还是 Pillow？
2. 卡片替代纯文本，还是图文都发？（默认 `image_only`）
3. 时段划分是否就用 07:00–19:00 明亮？
4. 条目数变化（如 20 条 / 40 条）时截图高度需自动适配，不能写死 1380。
5. 29 条长图在 QQ 可能被二次压缩，实机验证后再定是否 2x 渲染。
