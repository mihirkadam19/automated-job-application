import asyncio
import shutil
import socket
import subprocess
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, async_playwright

# Common install locations for a real, non-Playwright-managed Chrome on
# Windows - checked in order, falling back to a PATH lookup. Shared by
# login_capture.py (plain OS launch) and launch_subprocess_cdp_context
# below (plain OS launch + CDP attach).
_CHROME_PATHS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)


def find_chrome_executable() -> str | None:
    for path in _CHROME_PATHS:
        if Path(path).exists():
            return path
    return shutil.which("chrome") or shutil.which("google-chrome")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# The two ways job_search.py/apply_flow.py can drive a real browser against
# Indeed. "playwright" (Playwright's own chromium.launch()) is the default -
# it's simpler and faster since it skips the subprocess+CDP dance entirely.
# NOTE: earlier live testing this project confirmed Playwright's own
# launch() gets flagged by Cloudflare with zero exceptions, while "os_chrome"
# (launch_subprocess_cdp_context below) was the only mode confirmed to get
# past it. If a request using the default "playwright" mode comes back with
# a captcha checkpoint, either pass browser_mode="os_chrome" instead, or
# retry the same request headless=False so a human can clear the challenge
# in the visible browser window that opens.
BROWSER_MODES = ("playwright", "os_chrome")
DEFAULT_BROWSER_MODE = "playwright"


def launch(browser_mode: str, headless: bool, storage_state: dict | None = None):
    """Dispatches to the right launcher for browser_mode. Returns an async
    context manager (like launch_context/launch_subprocess_cdp_context
    themselves) - callers still do `async with browser_manager.launch(...)
    as context:`."""
    if browser_mode == "playwright":
        return launch_context(headless=headless, storage_state=storage_state)
    if browser_mode == "os_chrome":
        return launch_subprocess_cdp_context(headless=headless, storage_state=storage_state)
    raise ValueError(f"invalid browser_mode: {browser_mode!r} (expected one of {BROWSER_MODES})")


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


@asynccontextmanager
async def launch_subprocess_cdp_context(headless: bool, storage_state: dict | None = None):
    """Fallback launch mechanism for when launch_context's normal
    playwright.chromium.launch() gets flagged by Cloudflare's automation
    detection. Confirmed via a real trial: launching real Chrome as a plain
    OS subprocess with only --remote-debugging-port set, then having
    Playwright CONNECT to it afterward via connect_over_cdp, passed a live
    Cloudflare Turnstile check (and successfully scraped real search
    results) on the exact same session that launch_context's normal launch()
    got an instant CAPTCHA on moments earlier - despite both ending up with
    CDP attached. Playwright's launch() sets a number of its own additional
    flags/preferences beyond just the debugging port (automation-controlled
    switches, policy overrides, etc.) - one of those, not CDP attachment
    itself, appears to be the actual trigger. Only tried headed so far (a
    real human was present to clear an interactive challenge if one
    appeared); headless is passed through via --headless=new but is
    unverified. Uses a fresh temporary profile directory per call so it
    never collides with the user's real Chrome profile or other concurrent
    calls."""
    chrome_path = find_chrome_executable()
    if chrome_path is None:
        raise RuntimeError("could not locate a real Chrome executable for the CDP fallback")

    port = _free_port()
    profile_dir = tempfile.mkdtemp(prefix="indeed_cdp_profile_")

    # Confirmed via a real trial: without these, headless=True here hits
    # Indeed's own basic headless-Chromium bot-block outright ("Blocked -
    # Indeed.com", a completely different page than Cloudflare's Turnstile
    # interstitial, and one detect_challenge() didn't even recognize) -
    # this launcher never carried the two flags launch_context has used
    # since the very first bot-block fix of this whole project:
    # --disable-blink-features=AutomationControlled, and a normal desktop
    # Chrome User-Agent to replace the default "HeadlessChrome" one.
    args = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--disable-blink-features=AutomationControlled",
    ]
    if headless:
        args.append("--headless=new")
        args.append(f"--user-agent={DESKTOP_CHROME_UA}")
    args.append("about:blank")

    proc = subprocess.Popen(args)
    try:
        await asyncio.sleep(2)  # give Chrome a moment to open its debugging port
        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            if storage_state and storage_state.get("cookies"):
                await context.add_cookies(storage_state["cookies"])
            try:
                yield context
            finally:
                await context.close()
    finally:
        proc.terminate()
        shutil.rmtree(profile_dir, ignore_errors=True)
