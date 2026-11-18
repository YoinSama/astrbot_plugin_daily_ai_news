"""把 IssueInfo 填入 HTML 模板，产出可用于截图的临时 HTML。"""

from pathlib import Path
from typing import Optional

from .rss_source import IssueInfo

_TEMPLATE_NAME = "card.html"


def _default_template_path() -> Path:
    # 本文件位于 <plugin>/image_card/renderer.py，模板在 <plugin>/templates/card.html
    return Path(__file__).resolve().parent.parent / "templates" / _TEMPLATE_NAME


def render_card(
    issue: IssueInfo,
    theme: str,
    out_html: Path,
    template_path: Optional[Path] = None,
) -> Path:
    """渲染卡片 HTML 到 out_html，返回该路径。

    theme 写入 body 的 class；模板内 CSS 变量按 .light/.dark 切换。
    条数完全由 issue.items 决定（顶部计数与列表行同步）。
    """
    tpl_path = template_path or _default_template_path()
    with open(tpl_path, "r", encoding="utf-8") as f:
        tpl = f.read()

    rows = "\n".join(
        f'    <div class="item"><div class="num">{item["index"]:02d}</div>'
        f'<div class="t">{item["title"]}</div></div>'
        for item in issue.items
    )

    rendered = (
        tpl.replace("{{THEME}}", "dark" if theme == "dark" else "light")
        .replace("{{DATE}}", issue.date)
        .replace("{{COUNT}}", str(len(issue.items)))
        .replace("{{LINK}}", issue.link)
        .replace("{{ROWS}}", rows)
    )

    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(rendered)
    return out_html
