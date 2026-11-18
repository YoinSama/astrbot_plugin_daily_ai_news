"""从 RSS 首条 item 的 content:encoded 解析整期概览列表。

条数不固定：RSS 里有几个 <li> 就返回几条，不写死。
"""

import html as html_lib
import re
from dataclasses import dataclass
from typing import List

OVERVIEW_MARKER = '<h2 id="s1">概览</h2>'


@dataclass
class IssueInfo:
    date: str          # item 的 title，如 "2026-11-18"
    link: str          # item 的 link（原文链接）
    items: List[dict]  # [{"index": 1, "title": "..."}, ...]


def parse_overview(encoded_raw: str, date: str, link: str) -> IssueInfo:
    """解析 content:encoded 概览区的 <li>，返回 IssueInfo。

    与 previews/gen_from_rss.py 的验证逻辑一致：
    截到概览标记之后，逐个 <li> 去链接/序号/标签，反转义并合并空白。
    """
    if not encoded_raw or OVERVIEW_MARKER not in encoded_raw:
        return IssueInfo(date=date, link=link, items=[])

    overview = encoded_raw.split(OVERVIEW_MARKER, 1)[1]
    items: List[dict] = []
    for m in re.finditer(r"<li>(.*?)</li>", overview, re.S):
        raw = m.group(1)
        clean = re.sub(r"<a[^>]*>.*?</a>", "", raw, flags=re.S)      # 去 ↗ 链接
        clean = re.sub(r"<code>.*?</code>", "", clean, flags=re.S)   # 去 #N 序号
        clean = re.sub(r"<[^>]+>", "", clean)                        # 去其余标签
        clean = html_lib.unescape(clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        if clean:
            items.append({"index": len(items) + 1, "title": clean})

    return IssueInfo(date=date, link=link, items=items)
