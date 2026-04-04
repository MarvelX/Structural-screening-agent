from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "showcase" / "assets"
APP_URL = "http://localhost:8503"


def _wait_for_ready_state(page) -> None:
    page.goto(APP_URL, wait_until="networkidle")
    page.set_viewport_size({"width": 1600, "height": 1400})
    page.get_by_text("门式刚架屋面光伏增载初筛").wait_for(timeout=15000)
    page.get_by_role("tab", name="评估结论").wait_for(timeout=15000)


def _dismiss_streamlit_overlays(page) -> None:
    for label in ("Close sidebar", "关闭侧边栏"):
        button = page.get_by_label(label)
        if button.count():
            try:
                button.first.click(timeout=1000)
                break
            except PlaywrightTimeoutError:
                continue


def _capture_tab(page, tab_name: str, output_name: str) -> None:
    page.get_by_role("tab", name=tab_name).click()
    page.wait_for_timeout(800)
    page.screenshot(path=str(ASSET_DIR / output_name), clip={"x": 0, "y": 0, "width": 1600, "height": 1280})


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        _wait_for_ready_state(page)
        _dismiss_streamlit_overlays(page)
        _capture_tab(page, "评估结论", "assessment-overview.png")
        _capture_tab(page, "依据与追溯", "basis-traceability.png")
        _capture_tab(page, "报告导出", "report-export.png")
        browser.close()


if __name__ == "__main__":
    main()
