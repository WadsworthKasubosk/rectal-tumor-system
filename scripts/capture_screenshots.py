"""Capture system screenshots using Playwright."""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "figures" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000"

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        # 1 - Login page
        print("Capturing: Login page...")
        await page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=SCREENSHOT_DIR / "6-1_login.png", full_page=True)

        # Try to log in
        try:
            await page.fill('input[type="text"], input[placeholder*="用户"], input[placeholder*="username"]', "admin")
            await page.fill('input[type="password"]', "admin123")
            await page.click('button:has-text("登录"), button:has-text("Login")')
            await page.wait_for_timeout(3000)

            # 2 - Dashboard
            print("Capturing: Dashboard...")
            await page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=SCREENSHOT_DIR / "6-2_dashboard.png", full_page=True)

            # 3 - AI Diagnosis page
            print("Capturing: Diagnosis page...")
            await page.goto(f"{BASE_URL}/diagnosis", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=SCREENSHOT_DIR / "6-3_diagnosis.png", full_page=True)

            # 4 - Model Compare page
            print("Capturing: Model Compare page...")
            await page.goto(f"{BASE_URL}/compare", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=SCREENSHOT_DIR / "6-5_compare.png", full_page=True)

            # 5 - Case List page
            print("Capturing: Case List page...")
            await page.goto(f"{BASE_URL}/cases", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=SCREENSHOT_DIR / "6-6_cases.png", full_page=True)

            # 6 - Settings page
            print("Capturing: Settings page...")
            await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=SCREENSHOT_DIR / "6-10_settings.png", full_page=True)
        except Exception as e:
            print(f"Login/navigation failed: {e}")

        # 7 - Swagger API docs
        print("Capturing: Swagger API docs...")
        await page.goto(f"{API_URL}/docs", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=SCREENSHOT_DIR / "6-11_swagger.png", full_page=True)

        await browser.close()
        print(f"Done! {len(list(SCREENSHOT_DIR.glob('*.png')))} screenshots saved to {SCREENSHOT_DIR}")

asyncio.run(capture())
