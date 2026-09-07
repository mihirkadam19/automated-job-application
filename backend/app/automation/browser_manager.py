from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, async_playwright

# Playwright's default headless Chromium sends a User-Agent containing
# "HeadlessChrome", which Indeed's bot protection flags outright on
# search/listing pages (confirmed: identical cookies + headless=True was
# blocked with the default UA, but succeeded once this override was added -
# --headless=new was also tried and made no difference). Overriding the UA to
# a normal desktop Chrome string is what actually avoids the block headlessly.
DESKTOP_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@asynccontextmanager
async def launch_context(headless: bool, storage_state: dict | None = None, browser_type: str = "chromium"):
    """browser_type picks which Playwright-driven engine to launch.
    Chromium (default) is what job_search/apply_flow use throughout - it's
    proven to work fine there with an already-authenticated storage_state.
    "firefox" exists specifically for login_capture.py: confirmed via a real
    trial that Cloudflare's Turnstile checkbox on the login page kept
    resetting itself under Chromium even when a human genuinely clicked it -
    consistent with Cloudflare fingerprinting the CDP attachment Chromium
    automation uses, not whether a human is present. Firefox automation in
    Playwright uses a different protocol (Juggler) with no CDP involved at
    all, so it's worth trying specifically where that block was observed."""
    async with async_playwright() as playwright:
        if browser_type == "chromium":
            # Plain headless Chromium also gets an outright "Blocked" page on
            # other pages (e.g. login) before any content renders. Launching
            # the real installed Chrome build and disabling the
            # AutomationControlled blink feature is enough to render
            # normally there - confirmed against the live login page.
            browser: Browser = await playwright.chromium.launch(
                channel="chrome",
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
        else:
            browser = await getattr(playwright, browser_type).launch(headless=headless)
        try:
            context: BrowserContext = await browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                user_agent=DESKTOP_CHROME_UA if (headless and browser_type == "chromium") else None,
            )
            try:
                yield context
            finally:
                await context.close()
        finally:
            await browser.close()
