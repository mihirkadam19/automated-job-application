from playwright.async_api import Page

from app.automation.browser_manager import launch_context
from app.automation.challenge_detection import ChallengeDetected, detect_challenge

MAX_STEPS = 10
STEP_SETTLE_MS = 2500

# Priority order of "advance to the next step" button labels. Only the first
# one confirmed via a real trial: on the structured-data-intro step, no
# "Continue" button is visible, only "Review details" - trying labels in
# order and taking whichever is actually visible handles both.
GENERIC_CONTINUE_LABELS = ("Continue", "Review details", "Next")

# Best-effort field matching for any step we haven't seen for real (e.g. a
# contact-info or custom screening-question step) - unverified, since every
# real trial so far skipped straight from resume review to final submit.
FIELD_KEYWORDS = {
    "email": ("email",),
    "phone": ("phone", "tel"),
    "full_name": ("name",),
}


async def _click_visible(page: Page, label: str) -> bool:
    locator = page.get_by_role("button", name=label, exact=True).locator("visible=true")
    if await locator.count() == 0:
        return False
    await locator.first.click()
    return True


async def _handle_resume_selection(page: Page, resume_path: str | None) -> None:
    if resume_path is not None:
        file_input = page.locator("input[type=file]").first
        await file_input.set_input_files(resume_path)
    else:
        radios = page.locator("input[type=radio][name='resume-selection']")
        if await radios.count() > 0:
            # The native radio is visually hidden behind a styled card UI and
            # sits outside the viewport, so even check(force=True) fails -
            # confirmed via a real trial. Set state directly via the DOM and
            # fire the events React's controlled input listens for.
            await radios.first.evaluate(
                "el => { el.checked = true; "
                "el.dispatchEvent(new Event('input', { bubbles: true })); "
                "el.dispatchEvent(new Event('change', { bubbles: true })); }"
            )
    await page.wait_for_timeout(1000)
    await _click_visible(page, "Continue")


async def _handle_generic_step(page: Page, profile: dict) -> bool:
    for field, keywords in FIELD_KEYWORDS.items():
        value = profile.get(field)
        if not value:
            continue
        for keyword in keywords:
            inputs = page.locator(f"input[name*='{keyword}' i]:visible")
            if await inputs.count() > 0:
                current = await inputs.first.input_value()
                if not current:
                    await inputs.first.fill(str(value))

    for label in GENERIC_CONTINUE_LABELS:
        if await _click_visible(page, label):
            return True
    return False


async def apply_to_job(
    storage_state: dict,
    job_url: str,
    profile: dict,
    resume_path: str | None = None,
    headless: bool = True,
) -> dict:
    """Drive Indeed's native apply wizard using an already-authenticated
    session. Only supports jobs with a native "Apply with Indeed" flow -
    "Apply on company site" jobs redirect to an arbitrary third-party site
    and are reported as unsupported rather than attempted. Raises
    ChallengeDetected if Indeed shows a CAPTCHA/verification mid-flow.

    An earlier trial found the final submit button stuck disabled in
    headless mode and enabled in headed mode, which looked like a
    headless-specific gate - but a later trial showed the same "disabled"
    outcome in headed mode too, on a run that turned out to have hit a real
    reCAPTCHA checkbox challenge_detection wasn't catching yet (now fixed).
    So headed was never the actual fix; it was a missed CAPTCHA. headless
    defaults to True here to match job_search.py, with the caller free to
    force headed=False if they want to watch/solve a challenge live."""
    async with launch_context(headless=headless, storage_state=storage_state) as context:
        page = await context.new_page()
        await page.goto(job_url, timeout=30000)
        await page.wait_for_timeout(2000)

        apply_button = page.get_by_role("button", name="Apply with Indeed").locator(
            "visible=true"
        )
        if await apply_button.count() == 0:
            return {"status": "unsupported", "reason": "no native Indeed Apply flow for this job"}

        await apply_button.first.click()
        await page.wait_for_timeout(STEP_SETTLE_MS)

        for _ in range(MAX_STEPS):
            challenge = await detect_challenge(page)
            if challenge is not None:
                raise ChallengeDetected(challenge)

            url = page.url

            if "review-module" in url:
                await page.wait_for_timeout(STEP_SETTLE_MS)
                submitted = await _click_visible(page, "Submit your application")
                if submitted:
                    return {"status": "submitted"}
                return {"status": "failed", "reason": "could not find submit button on review step"}

            if "resume-selection" in url:
                await _handle_resume_selection(page, resume_path)
                await page.wait_for_timeout(STEP_SETTLE_MS)
                continue

            if "questions-module" in url:
                # Confirmed via a real trial: employer-custom screening
                # questions (arbitrary text, radio groups + free-text
                # inputs), required before Continue does anything. No
                # generic way to answer these reliably from a profile -
                # fail fast rather than loop uselessly to MAX_STEPS.
                return {
                    "status": "manual_action_required",
                    "reason": f"custom screening questions need a human at {url}",
                }

            advanced = await _handle_generic_step(page, profile)
            if not advanced:
                return {"status": "failed", "reason": f"no actionable step found at {url}"}
            await page.wait_for_timeout(STEP_SETTLE_MS)

        return {"status": "failed", "reason": "exceeded max steps without reaching submission"}
