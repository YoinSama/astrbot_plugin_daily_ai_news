"""主题判定：按配置时间段在明亮 / 暗黑之间切换。"""

from datetime import datetime
from typing import Tuple


def _parse_hhmm(value: str, fallback: Tuple[int, int]) -> Tuple[int, int]:
    """把 'HH:MM' 解析为 (hour, minute)，失败时用默认值。"""
    try:
        hour, minute = value.strip().split(":")
        h, m = int(hour), int(minute)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except (ValueError, AttributeError):
        pass
    return fallback


def resolve_theme(
    now: datetime,
    mode: str,
    light_start: str,
    dark_start: str,
) -> str:
    """返回 'light' 或 'dark'。

    mode:
      - 'light' / 'dark'：锁定主题
      - 'auto'（其他值同样按 auto 处理）：按本地时间段判定
        [light_start, dark_start) -> light，其余 -> dark；
        支持 dark_start < light_start 的夜间跨午夜场景。
    """
    if mode in ("light", "dark"):
        return mode

    lh, lm = _parse_hhmm(light_start, (7, 0))
    dh, dm = _parse_hhmm(dark_start, (18, 0))
    light_min = lh * 60 + lm
    dark_min = dh * 60 + dm
    now_min = now.hour * 60 + now.minute

    if light_min <= dark_min:
        return "light" if light_min <= now_min < dark_min else "dark"
    # 夜间段跨午夜：如 light=07:00, dark=22:00 时暗色为 [22:00, 07:00)
    return "dark" if now_min >= dark_min or now_min < light_min else "light"
