import asyncio
import urllib.parse

from playwright.async_api import BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.browser_manager import launch_subprocess_cdp_context
from app.automation.challenge_detection import ChallengeDetected, detect_challenge

SEARCH_URL = "https://www.indeed.com/jobs"

# Confirmed via a real trial against the live, authenticated search page.
JOB_CARD_SELECTOR = "div.job_seen_beacon"
TITLE_LINK_SELECTOR = "h3.jobTitle a"
COMPANY_SELECTOR = "span[data-testid='company-name']"
LOCATION_SELECTOR = "div[data-testid='text-location']"

CHALLENGE_WAIT_TIMEOUT_SECONDS = 180
CHALLENGE_POLL_INTERVAL_SECONDS = 3


async def _run_search(
    context: BrowserContext, url: str, limit: int, wait_for_human: bool = False
) -> list[dict]:
    page = await context.new_page()
    await page.goto(url, timeout=30000)

    challenge = await detect_challenge(page)
    if challenge is not None and wait_for_human:
        # The fallback path exists specifically because a real human can be
        # present to clear an interactive challenge (confirmed via a real
        # trial) - the immediate single check below is right for the
        # primary, unattended path, but would never give that human a
        # chance here.
        elapsed = 0
        while challenge is not None and elapsed < CHALLENGE_WAIT_TIMEOUT_SECONDS:
            await asyncio.sleep(CHALLENGE_POLL_INTERVAL_SECONDS)
            elapsed += CHALLENGE_POLL_INTERVAL_SECONDS
            challenge = await detect_challenge(page)

    if challenge is not None:
        raise ChallengeDetected(challenge)

    try:
        await page.wait_for_selector(JOB_CARD_SELECTOR, timeout=10000)
    except PlaywrightTimeoutError:
        return []

    cards = page.locator(JOB_CARD_SELECTOR)
    count = min(await cards.count(), limit)

    jobs = []
    for i in range(count):
        card = cards.nth(i)

        link = card.locator(TITLE_LINK_SELECTOR).first
        job_key = await link.get_attribute("data-jk")
        title = (await link.inner_text()).strip()

        company_el = card.locator(COMPANY_SELECTOR).first
        company = (await company_el.inner_text()).strip() if await company_el.count() else ""

        location_el = card.locator(LOCATION_SELECTOR).first
        job_location = (
            (await location_el.inner_text()).strip() if await location_el.count() else ""
        )

        jobs.append(
            {
                "external_job_id": job_key,
                "title": title,
                "company": company,
                "location": job_location,
                "job_url": f"https://www.indeed.com/viewjob?jk={job_key}" if job_key else None,
            }
        )

    return jobs


async def search_jobs(
    storage_state: dict, query: str, location: str = "", limit: int = 10, headless: bool = True
) -> list[dict]:
    """Search Indeed using an already-authenticated session. Read-only -
    nothing is persisted or submitted here. Launches via
    launch_subprocess_cdp_context rather than Playwright's own
    chromium.launch() - confirmed via extensive real trials that launch()
    gets flagged by Cloudflare's automation detection every single time,
    with zero exceptions all session, while a plain subprocess-launched
    Chrome connected to afterward via connect_over_cdp has passed
    repeatedly. When headless=False, waits for a human to clear anything
    Cloudflare shows; still raises ChallengeDetected if it never clears (or
    immediately when headless=True, since no one's there to clear it)."""
    params = urllib.parse.urlencode({"q": query, "l": location})
    url = f"{SEARCH_URL}?{params}"

    async with launch_subprocess_cdp_context(headless=headless, storage_state=storage_state) as context:
        return await _run_search(context, url, limit, wait_for_human=not headless)
