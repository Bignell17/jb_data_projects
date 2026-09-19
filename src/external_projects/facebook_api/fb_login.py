import asyncio
from playwright.async_api import async_playwright

async def login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.facebook.com")
        input("Log in manually, then press ENTER...")

        await context.storage_state(path="fb_state.json")
        await browser.close()

asyncio.run(login())