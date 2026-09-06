import urllib.parse

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.browser_manager import launch_context
from app.automation.challenge_detection import ChallengeDetected, detect_challenge

SEARCH_URL = "https://www.indeed.com/jobs"

# Confirmed via a real trial against the live, authenticated search page.
JOB_CARD_SELECTOR = "div.job_seen_beacon"
TITLE_LINK_SELECTOR = "h3.jobTitle a"
COMPANY_SELECTOR = "span[data-testid='company-name']"
LOCATION_SELECTOR = "div[data-testid='text-location']"


async def search_jobs(
    storage_state: dict, query: str, location: str = "", limit: int = 10
) -> list[dict]:
    """Search Indeed using an already-authenticated session. Read-only -
    nothing is persisted or submitted here. Raises ChallengeDetected if
    Indeed shows a CAPTCHA/verification instead of results."""
    params = urllib.parse.urlencode({"q": query, "l": location})
    url = f"{SEARCH_URL}?{params}"

    async with launch_context(headless=True, storage_state=storage_state) as context:
        page = await context.new_page()
        await page.goto(url, timeout=30000)

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
