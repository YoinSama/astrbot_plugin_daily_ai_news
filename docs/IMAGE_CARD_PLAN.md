# AI 早报图片卡片功能 · 开发方案（待确认，尚未改代码）

> 状态：仅预览 + 方案，未修改 `main.py` / `_conf_schema.json` / `metadata.yaml` / `README.md`。
> 预览文件：`previews/card_light.png`、`previews/card_dark.png`、`previews/card_compare.png`、
> `previews/image_card_preview.html`（均已被 `.gitignore` 的 `previews/` 规则忽略）。

## 1. 目标

在现有「纯文本早报」之外，新增一种**按文章内容生成的图片卡片**推送方式：

- 卡片正文来自已有 RSS 抓取 + AI 总结结果，不引入第二套数据源；
- 主题分**明亮 / 暗黑**两套，支持按配置的时间段自动切换；
- 背景图由**本地 Docker 部署的 T2I 服务**生成，文字层用 HTML/CSS 叠加（不让 T2I 生成文字，避免乱码）；
- 图片失败时自动降级回现有纯文本，不影响原推送链路。

## 2. 预览图对应的卡片结构

从上到下：

1. 顶部品牌条：`JUYA DAILY` + 日期胶囊；
2. 大标题「今日 AI 早报」+ 副标题；
3. T2I 背景图区域（当前预览里是 CSS 占位，实际由本地服务出图）；
4. `01–05` 编号的要点列表（来自 AI 总结）；
5. 页脚：来源、网址。

尺寸建议 720 × 1200（2x 渲染成 1440 × 2400 后再缩，抵消 QQ 压缩）。

## 3. 主题自动切换规则

新增配置项：

| 配置项 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `card_theme_mode` | string | `auto` | `auto` / `light` / `dark` |
| `card_light_start` | string | `07:00` | 明亮时段起点（本地时间 HH:MM） |
| `card_dark_start` | string | `19:00` | 暗黑时段起点（本地时间 HH:MM） |

判定伪代码（支持夜间跨午夜，例如 22:00 → 07:00）：

```python
def resolve_theme(now, mode, light_start, dark_start):
    if mode in ("light", "dark"):
        return mode
    t = now.time()
    if light_start <= dark_start:          # 白天段不跨午夜
        return "light" if light_start <= t < dark_start else "dark"
    return "dark" if t >= dark_start or t < light_start else "light"  # 夜间跨午夜
```

## 4. T2I 接入（待确认具体服务）

统一成一个适配器接口，屏蔽服务差异：

```python
class T2IProvider:
    async def generate(self, prompt: str, width: int, height: int, theme: str) -> str:
        """返回本地图片文件路径；失败抛异常由上层降级。"""
```

三种预设，按 `t2i_provider` 选择（**具体是哪一种需要你确认**）：

| provider | 对接方式 | 备注 |
| --- | --- | --- |
| `sdwebui` | `POST {endpoint}/sdapi/v1/txt2img` | 返回 `images[0]` base64，直接落盘 |
| `comfyui` | `POST {endpoint}/prompt` 提交 workflow → 轮询 `GET /history/{id}` → `GET /view` | 需要你提供 workflow JSON |
| `custom` | `POST {endpoint}` JSON `{prompt,width,height,theme}` | 返回 `{image_path}` 或 base64 |

其他配置：`t2i_endpoint`、`t2i_timeout`（秒）、`t2i_prompt_light`、`t2i_prompt_dark`、`t2i_cache_days`。

**提示词方向**（只生成背景，留出中部文字区）：
- 明亮：极简科技感、浅色留白、柔和蓝紫点缀、无文字、16:9；
- 暗黑：深蓝黑底、青色微光、抽象电路/数据流、无文字、16:9。

**缓存**：按 `{article_date}-{theme}` 命名，命中则跳过 T2I；过期文件按 `t2i_cache_days` 清理。缓存目录加入 `.gitignore`。

## 5. 渲染方案选型

| 方案 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- |
| HTML/CSS 模板 + 无头浏览器截图 | 中文排版可靠、样式改动直观、预览图即用此法 | 部署机需有 Edge/Chromium | **推荐** |
| Pillow 直接绘制 | 无浏览器依赖 | 中文换行/字距需手工处理，改版麻烦 | 备选（无浏览器时） |
| T2I 直接生成整卡 | 省事 | 文字必然乱码/错字 | 不采用 |

推荐流水线：

```
RSS 首条 item → 现有 AI 总结 → 拆成 5–8 条要点（JSON 结构化 prompt）
        → 选主题 → 取/生成 T2I 背景 → 填 HTML 模板 → Edge 无头截图 → PNG
        → MessageChain().image(path) 发送 → 失败降级纯文本
```

结构化 prompt 建议让 LLM 输出 `{"date": "...", "points": [{"title": "...", "desc": "..."}]}`，
比从自由文本里正则切分稳；失败时回退到现有纯文本总结。

## 6. 建议新增文件

```
image_card/
  __init__.py
  renderer.py       # HTML 模板填充 + 无头浏览器截图
  t2i.py            # T2I 适配器（sdwebui / comfyui / custom）
  themes.py         # 时间段 → 主题
templates/
  card.html         # 单一模板，CSS 变量切换明暗
previews/           # 已被 gitignore
generated/          # 运行时输出图片，新增 gitignore 规则
docs/IMAGE_CARD_PLAN.md
```

`main.py` 只增加：配置读取、一个 `@filter.command("ainews_card")`、在 `_do_push()` 里按开关分流；
原有纯文本路径保持可用。

## 7. 分阶段实施（等你确认后再动手）

1. **确认接口**：本地 Docker 里 T2I 具体服务、端口、API 形态；是否要 ComfyUI workflow。
2. **阶段 A**：不接 T2I，用纯色背景跑通「主题选择 → HTML → 截图 → 发图」。
3. **阶段 B**：接 T2I 生成背景 + 缓存 + 超时降级。
4. **阶段 C**：配置面板、手动指令、发送模式（仅图 / 图+文）、README 与 CHANGELOG。
5. **阶段 D**：实机 QQ 验证图片清晰度与发送成功率，调尺寸。

## 8. 待你确认的问题

1. 本地 Docker 的 T2I 是 **SD WebUI / ComfyUI / 自建接口**？地址和端口？
2. 卡片是**替代**纯文本，还是**图文都发**？
3. 明亮 / 暗黑的时间段就用 `07:00–19:00` 吗？
4. 生成方式是否接受「HTML + 无头浏览器截图」？部署机有没有 Edge/Chromium？
5. T2I 只画背景（推荐），还是要它参与整张卡片的视觉？

## 9. 无 T2I 模式（已实测可行）

不接 T2I 也完全能做：纯 HTML/CSS 排版 + 几何色块替代生成背景，再用 Edge 无头浏览器截图。
实例：`previews/issue_2026-11-18_s44.png`（720 × 1058，黑白双色，内容取自 2026-11-18 日报 `#s44`），
源文件 `previews/issue_2026-11-18_s44.html`。

- 优点：零外部依赖、文字 100% 准确、出图快、明暗/黑白主题随意扩展；
- 代价：背景视觉不如生成图丰富，靠排版、色块与字体层级弥补；
- 建议：新增 `t2i_provider = none` 作为默认模式，之后再按需切到 `sdwebui` / `comfyui` / `custom`。
