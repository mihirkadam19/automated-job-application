import re
import subprocess
import webbrowser

from playwright.async_api import Page

from app.automation.browser_manager import find_chrome_executable

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


def open_login_window() -> None:
    """Launches a genuinely plain, un-automated Chrome window at Indeed's
    login page - no Playwright, no CDP, no remote-debugging port, nothing
    attached to it at all. Confirmed via extensive real trials that every
    Playwright-driven variant (Chromium, Firefox, fresh profile, persistent
    profile, different IPs including a mobile hotspot) hit the same
    Cloudflare Turnstile wall regardless - the common factor was always the
    automation attachment itself, not the browser engine or network. A
    plain subprocess-launched Chrome has no automation protocol attached at
    all, so there is nothing for Cloudflare to flag - from its perspective
    this is indistinguishable from the human opening Chrome normally,
    because it is.

    Because nothing is attached to this window, we have no way to detect
    when login finishes or to read the resulting cookies programmatically -
    that's the trade-off for not looking automated. The human logs in
    completely normally here, then exports their cookies (e.g. via the
    Cookie-Editor extension) and hands them to session_service.import_session
    (POST /sessions/import) to actually populate the session row."""
    chrome_path = find_chrome_executable()
    if chrome_path:
        subprocess.Popen([chrome_path, LOGIN_URL])
    else:
        webbrowser.open(LOGIN_URL)
