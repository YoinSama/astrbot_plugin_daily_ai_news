"""用 Playwright 把卡片 HTML 截图为 PNG。

高度自适应：用 full_page=True 截取整页，不写死尺寸，
因此条目数变化（20 条 / 40 条）也不裁切。
"""

import asyncio
from pathlib import Path
from typing import Optional

WIDTH = 720


async def _launch_browser(playwright, browser_path: str = ""):
    """优先用指定的 Chromium/Edge，其次系统 Edge，最后 Playwright 自带 chromium。"""
    if browser_path and Path(browser_path).exists():
        return await playwright.chromium.launch(
            headless=True, executable_path=browser_path, args=["--disable-gpu"]
        )

    # 常见 Windows Edge 路径，避免强制用户先执行 playwright install
    edge_candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in edge_candidates:
        if Path(candidate).exists():
            try:
                return await playwright.chromium.launch(
                    headless=True, executable_path=candidate, args=["--disable-gpu"]
                )
            except Exception:
                pass  # 版本不兼容时继续尝试自带 chromium

    return await playwright.chromium.launch(headless=True, args=["--disable-gpu"])


async def screenshot_card(
    html_path: Path,
    png_path: Path,
    browser_path: str = "",
    width: int = WIDTH,
) -> Path:
    """渲染 HTML 并截图，返回 PNG 路径。"""
    from playwright.async_api import async_playwright

    html_path = Path(html_path)
    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        browser = await _launch_browser(playwright, browser_path)
        try:
            page = await browser.new_page(
                viewport={"width": width, "height": 900},
                device_scale_factor=1,
            )
            await page.goto(html_path.resolve().as_uri(), wait_until="load")
            # 等字体与样式稳定，避免截到未排版完成的画面
            await page.evaluate("() => document.fonts.ready")
            await page.screenshot(path=str(png_path), full_page=True)
        finally:
            await browser.close()

    return png_path
