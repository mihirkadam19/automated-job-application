from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, async_playwright


@asynccontextmanager
async def launch_context(headless: bool, storage_state: dict | None = None):
    async with async_playwright() as playwright:
        # Plain headless Chromium gets an outright "Blocked" page from Indeed's
        # bot protection before any content renders. Launching the real installed
        # Chrome build and disabling the AutomationControlled blink feature is
        # enough to render normally - confirmed against the live login page.
        browser: Browser = await playwright.chromium.launch(
            channel="chrome",
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            context: BrowserContext = await browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            try:
                yield context
            finally:
                await context.close()
        finally:
            await browser.close()
