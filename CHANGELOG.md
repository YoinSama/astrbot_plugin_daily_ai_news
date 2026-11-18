# Changelog

## [1.03] - 2026-11-19

### 新增
- **图片卡片推送模式**：新增 `push_mode` 配置（`text` / `image`，二选一，默认 `text`）。`image` 模式从 RSS 首条 `content:encoded` 的概览列表动态解析全部新闻条目（条数随源站变化，不写死），填入 HTML 模板后用 Playwright 截图成 PNG 发送，无需调用 LLM。
- **明暗双主题**：`card_theme_mode`（`auto`/`light`/`dark`），`auto` 默认 07:00–18:00 明亮、18:00–次日 07:00 暗黑；截图高度随条目数自适应。
- **手动出图指令**：`/ainews_card` 不受 `push_mode` 限制，随时生成图片卡片。

### 变更
- 新增依赖 `playwright`；截图优先使用系统 Edge，可配置 `card_browser_path`，无需即可自动探测。
- 图片生成失败时自动降级为纯文本推送，不影响原有链路。

## [1.02] - 2026-06-14

### 变更
- **RSS 源迁移**：更新橘鸦 AI 日报 RSS 订阅地址为 `https://daily.juya.uk/rss.xml`，替换已废弃的旧地址。
- **完整正文解析**：适配新 RSS 源的 `content:encoded` 字段，优先读取完整正文，缺失时回退到 `description` 摘要。
- **日期识别优化**：优先使用标题中的 `YYYY-MM-DD` 日期，避免发布时间时区差影响当日推送判断。

## [1.01] - 2026-03-12

### 新增
- **多平台支持**：订阅目标支持群聊（`GroupMessage`）与私聊（`FriendMessage`）两种类型，可在配置中分别填写群聊 ID 与私聊账号 ID，格式兼容 `{机器人名称}:{ID}`、纯数字等多种写法。
- **AI 总结开关**：新增 `enable_ai_summary` 配置项，可关闭 AI 总结功能，关闭后直接推送原文摘要，不再调用 LLM。
