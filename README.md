# astrbot_plugin_daily_ai_news

> ## 🔀 相对上游仓库的修改
>
> 本仓库是对上游 [xxofficial/astrbot_plugin_daily_ai_news](https://github.com/xxofficial/astrbot_plugin_daily_ai_news) 的 fork，在此基础上的改动如下：
>
> | # | 改动 | 说明 |
> | --- | --- | --- |
> | 1 | **修复安装失败** | 上游 `metadata.yaml` 的 `version: 1.02` 被 YAML 解析为 float，导致新版 AstrBot 报「version 必须是非空字符串」；本仓库改为合法字符串（现为 `v1.0.3`），可正常安装。 |
> | 2 | **新增图片卡片推送模式** | 新增 `push_mode` 配置（`text` 纯文本 / `image` 图片卡片，二选一）。`image` 模式从 RSS 首条 `content:encoded` 的概览列表动态解析全部新闻条目（条数随源站变化，非写死），填入 HTML 模板后用 **Playwright 截图**成 PNG 发送，**无需调用 LLM**。 |
> | 3 | **明暗双主题 + 时段自动切换** | 新增 `card_theme_mode` / `card_light_start` / `card_dark_start`，`auto` 默认 07:00–18:00 明亮、18:00–次日 07:00 暗黑；截图高度随条目数自适应。 |
> | 4 | **新增 `/ainews_card` 指令** | 手动触发生成图片卡片，不受 `push_mode` 限制。 |
> | 5 | **失败降级** | 图片卡片生成失败时自动回退为原纯文本推送，不影响原有链路。 |
> | 6 | **改用相对导入** | 子模块导入由绝对路径改为 `from .image_card import ...`，修复 AstrBot 以包方式加载插件时报 `No module named 'image_card'`。 |
> | 7 | **配置项改为下拉栏** | `push_mode`、`card_theme_mode` 在管理面板中显示为下拉选择（`options`）。 |
> | 8 | **更新源指向本 fork** | `metadata.yaml` 的 `repo` 由上游改为本仓库地址，面板「更新」从本 fork 拉取。 |
> | 9 | **忽略本地产物** | `.gitignore` 增加 `previews/`、`generated/`、图片格式等，生成的预览图/截图不入库。 |
>
> 新增依赖：`playwright`。详见 [CHANGELOG.md](CHANGELOG.md) 的 `1.03` 条目。

每日 AI 资讯自动推送插件 - 为 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 开发

通过 RSS 订阅 [橘鸦 AI 日报](https://daily.juya.uk/rss.xml) 获取最新 AI 早报，经 **AI 总结** 后自动推送到 QQ 群 / 私聊。

## ✨ 功能

- 📰 **每日自动推送**：每天定时（默认早 8:00）自动推送最新 AI 资讯
- 🤖 **AI 智能总结**：调用 AstrBot 内置 LLM，将长篇早报精炼为 5-8 条关键要点
- 🔄 **手动获取**：发送 `/ainews` 随时获取最新 AI 资讯
- 📋 **灵活订阅**：支持配置文件填写群号/QQ号 + 群内指令订阅两种方式
- ⏳ **智能轮询**：若 RSS 尚未更新当日内容，插件会自动间隔轮询直到获取到当日文章
- 💾 **缓存去重**：AI 总结结果会缓存到本地，避免重复调用 LLM；已推送文章自动去重
- 🖼️ **图片卡片模式**：可切换为「整期概览图片卡片」推送——从 RSS 首条的 `content:encoded` 解析全部新闻条目（条数随源站动态变化），填入 HTML 模板后用 Playwright 截图成 PNG 发送，明暗主题可按时间段自动切换
- 🎨 **明暗双主题**：明亮 / 暗黑两套样式，`auto` 模式默认 07:00–18:00 明亮、18:00–次日 07:00 暗黑

## 📝 指令列表

| 指令             | 说明                              |
| ---------------- | --------------------------------- |
| `/ainews`        | 立即获取最新 AI 资讯（按当前推送模式）         |
| `/ainews_card`   | 立即生成图片卡片（不受推送模式影响，始终出图） |
| `/ainews_sub`    | 订阅每日推送（群聊/私聊均可使用）              |
| `/ainews_unsub`  | 取消每日推送订阅                               |
| `/ainews_status` | 查看推送状态与订阅信息                         |

## ⚙️ 配置说明

安装插件后，在 AstrBot 管理面板中可配置以下选项：

| 配置项                             | 说明                                                              | 默认值 |
| ---------------------------------- | ----------------------------------------------------------------- | ------ |
| `push_hour` 每日推送时间（小时）   | 0-23，设定首次检查 RSS 的小时                                     | 8      |
| `push_minute` 每日推送时间（分钟） | 0-59，设定首次检查 RSS 的分钟                                     | 0      |
| `rss_poll_interval` RSS 轮询间隔   | 当 RSS 尚未更新当日内容时，每隔多少秒重新检查一次（默认 10 分钟） | 600    |
| `push_mode` 推送模式               | `text`=纯文本 AI 总结；`image`=图片卡片。两者二选一               | `text` |
| `card_theme_mode` 卡片主题模式     | `auto`=按时段自动；`light`=始终明亮；`dark`=始终暗黑               | `auto` |
| `card_light_start` 明亮开始时间    | `auto` 下明亮主题起点，HH:MM                                      | `07:00`|
| `card_dark_start` 暗黑开始时间     | `auto` 下暗黑主题起点，HH:MM（至次日明亮起点）                    | `18:00`|
| `card_browser_path` 截图浏览器路径 | Playwright 使用的 Chromium/Edge 路径；留空自动探测系统 Edge       | 空     |
| `subscribed_groups` 订阅群号       | 手动填写需要推送的 QQ 群号，每行一个                              | 空     |
| `subscribed_users` 订阅 QQ 号      | 手动填写需要私聊推送的 QQ 号，每行一个                            | 空     |

## 📦 安装

1. 在 AstrBot 管理面板中搜索 `astrbot_plugin_daily_ai_news` 安装
2. 或手动将本仓库克隆到 `addons/plugins/` 目录下
3. 重启 AstrBot 即可生效

## 📌 注意事项

- **需要配置 LLM**：`push_mode=text` 时 AI 总结依赖 AstrBot 中已配置的 LLM Provider；`push_mode=image` 不需要 LLM
- **图片卡片依赖浏览器**：`push_mode=image` 用 Playwright 截图，需系统装有 Edge/Chromium，或先执行 `playwright install chromium`；插件会在安装依赖时自动带上 `playwright` 包（需 AstrBot 环境允许安装依赖）
- 若 AI 总结失败，插件会自动回退使用原文摘要进行推送；若图片卡片生成失败，会降级为纯文本推送
- 插件在重启后会自动补偿检查：若已过推送时间且当天未推送，会立即尝试拉取并推送
- 配置群号方式需要填写 QQ 群号码（纯数字），指令方式需在群内发送 `/ainews_sub`
- 两种订阅方式（配置文件 + 指令）可同时使用，插件会自动合并去重
- AI 总结缓存最多保留最近 10 天的记录

## 📝 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)。

## 📄 License

[GPL-3.0](LICENSE)
