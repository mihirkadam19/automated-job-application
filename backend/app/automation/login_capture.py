import asyncio
import re

from playwright.async_api import Page

from app.config import get_settings
from app.automation.browser_manager import launch_context

LOGIN_URL = "https://secure.indeed.com/auth"

# A page only a logged-in session can stay on - confirmed via a real login
# trial (Indeed lands here post-login, at least sometimes). Used by
# session_service.refresh() as a cheap "is this stored session still good"
# check.
ACCOUNT_URL = "https://secure.indeed.com/settings/account"

# secure.indeed.com hosts both the login page itself AND legitimate
# authenticated pages (e.g. /settings/account, confirmed via a real login
# trial) - so the check has to target the login path specifically, not the
# whole subdomain. Only "/auth" is confirmed from real trials; other paths
# here are unverified guesses at other pre-login steps.
NOT_LOGGED_IN_PATTERN = re.compile(r"secure\.indeed\.com/(auth|account/verify|challenge|checkpoint)")


def looks_logged_in(page: Page) -> bool:
    return not NOT_LOGGED_IN_PATTERN.search(page.url)


async def _wait_for_manual_login(page: Page) -> bool:
    settings = get_settings()
    elapsed = 0.0
    while elapsed < settings.login_wait_timeout_seconds:
        if looks_logged_in(page):
            return True
        await asyncio.sleep(settings.login_poll_interval_seconds)
        elapsed += settings.login_poll_interval_seconds
    return looks_logged_in(page)


async def capture_login_session() -> dict | None:
    """Open a fresh, isolated browser window for a human to log into Indeed
    manually (password, SMS/email code, CAPTCHA - whatever Indeed asks for,
    handled entirely by the human). Returns the resulting storage_state once
    login is detected, or None if nobody finished within the timeout."""
    async with launch_context(headless=False) as context:
        page = await context.new_page()
        await page.goto(LOGIN_URL)
        logged_in = await _wait_for_manual_login(page)
        if not logged_in:
            return None
        return await context.storage_state()
