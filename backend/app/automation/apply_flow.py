import asyncio

from playwright.async_api import Page

from app.automation.browser_manager import launch_context
from app.automation.challenge_detection import ChallengeDetected, detect_challenge
from app.automation.screening_answers import _SET_CHECKED_JS, answer_questions

MAX_STEPS = 10
STEP_SETTLE_MS = 2500
MANUAL_PAUSE_POLL_INTERVAL_SECONDS = 2

# Confirmed via a real trial: on the review step, a genuine reCAPTCHA
# Enterprise checkbox anchor frame (type=image&size=normal - an actual
# widget, not the harmless invisible badge) was present in the DOM, but
# detect_challenge() missed it both times it was checked here (once at the
# top of this loop iteration, once right above) and fell through to "no
# challenge detected". A follow-up manual inspection a few seconds later
# found the exact same #recaptcha-anchor checkbox _recaptcha_checkbox_present
# already knows how to recognize - so the selector logic itself is fine, the
# widget just hadn't finished mounting inside its iframe within the ~2.5s
# gap between checks. Poll a few more times before concluding there's truly
# no challenge to blame for the disabled button.
SUBMIT_DISABLED_RETRY_ATTEMPTS = 4
SUBMIT_DISABLED_RETRY_MS = 1500

# Priority order of "advance to the next step" button labels - confirmed
# via real trials that this varies by step: "Continue" on most steps, no
# "Continue" on structured-data-intro (only "Review details"), and the
# demographic/consent step uses "Review your application" instead of
# either. Trying labels in order and taking whichever is actually visible
# handles all of these without hardcoding per-step button names.
GENERIC_CONTINUE_LABELS = ("Continue", "Review details", "Review your application", "Next")

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
            # confirmed via a real trial. _SET_CHECKED_JS also bypasses
            # React's instance-patched setter so its internal tracker
            # actually registers the change (see screening_answers.py).
            await radios.first.evaluate(_SET_CHECKED_JS)
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


async def _wait_for_human(page: Page) -> str:
    """Only used when pause_on_manual=True: leaves the browser open exactly
    where the automated flow stalled - no navigation, no re-attempt from
    scratch - and polls until the human closes the tab, tracking the last
    URL seen so the caller can tell whether they actually finished (reached
    Indeed's real post-apply confirmation) or just walked away."""
    last_url = page.url
    while not page.is_closed():
        try:
            last_url = page.url
        except Exception:
            pass
        await asyncio.sleep(MANUAL_PAUSE_POLL_INTERVAL_SECONDS)
    return last_url


async def _resolve_pause(page: Page, reason: str, checkpoint_type: str) -> dict:
    last_url = await _wait_for_human(page)
    if "post-apply" in last_url:
        return {"status": "submitted"}
    return {"status": "manual_action_required", "reason": reason, "checkpoint_type": checkpoint_type}


async def apply_to_job(
    storage_state: dict,
    job_url: str,
    profile: dict,
    resume_path: str | None = None,
    headless: bool = True,
    pause_on_manual: bool = False,
) -> dict:
    """Drive Indeed's native apply wizard using an already-authenticated
    session. Only supports jobs with a native "Apply with Indeed" flow -
    "Apply on company site" jobs redirect to an arbitrary third-party site
    and are reported as unsupported rather than attempted. Raises
    ChallengeDetected if Indeed shows a CAPTCHA/verification mid-flow,
    unless pause_on_manual is set (see below).

    An earlier trial found the final submit button stuck disabled in
    headless mode and enabled in headed mode, which looked like a
    headless-specific gate - but a later trial showed the same "disabled"
    outcome in headed mode too, on a run that turned out to have hit a real
    reCAPTCHA checkbox challenge_detection wasn't catching yet (now fixed).
    So headed was never the actual fix; it was a missed CAPTCHA. headless
    defaults to True here to match job_search.py, with the caller free to
    force headed=False if they want to watch/solve a challenge live.

    pause_on_manual is for the "resume manually" flow: instead of raising/
    returning the moment something needs a human (a challenge, an
    unanswerable screening question, a stuck submit button, an unrecognized
    step), the browser is left open exactly on that page and this function
    blocks until the human closes it - so a human takes over mid-wizard
    instead of restarting the whole application from the job posting. Only
    makes sense paired with headless=False."""
    async with launch_context(headless=headless, storage_state=storage_state) as context:
        page = await context.new_page()
        await page.goto(job_url, timeout=30000)
        await page.wait_for_timeout(2000)

        apply_button = page.get_by_role("button", name="Apply with Indeed").locator(
            "visible=true"
        )
        if await apply_button.count() == 0:
            if pause_on_manual:
                return await _resolve_pause(
                    page, "no native Indeed Apply flow for this job", "unknown_challenge"
                )
            return {"status": "unsupported", "reason": "no native Indeed Apply flow for this job"}

        await apply_button.first.click()
        await page.wait_for_timeout(STEP_SETTLE_MS)

        for _ in range(MAX_STEPS):
            challenge = await detect_challenge(page)
            if challenge is not None:
                if pause_on_manual:
                    return await _resolve_pause(
                        page, f"challenge detected: {challenge.value}", challenge.value
                    )
                raise ChallengeDetected(challenge)

            url = page.url

            if "review-module" in url:
                await page.wait_for_timeout(STEP_SETTLE_MS)

                # Re-check right before the highest-stakes action: a
                # challenge can appear in the gap between this iteration's
                # top-of-loop check and now - confirmed via a real trial
                # where the submit click timed out on a disabled button
                # instead of a challenge ever being raised.
                challenge = await detect_challenge(page)
                if challenge is not None:
                    if pause_on_manual:
                        return await _resolve_pause(
                            page, f"challenge detected: {challenge.value}", challenge.value
                        )
                    raise ChallengeDetected(challenge)

                submit_button = page.get_by_role(
                    "button", name="Submit your application", exact=True
                ).locator("visible=true")
                if await submit_button.count() == 0:
                    if pause_on_manual:
                        return await _resolve_pause(
                            page, "could not find submit button on review step", "unknown_challenge"
                        )
                    return {"status": "failed", "reason": "could not find submit button on review step"}
                if await submit_button.first.get_attribute("disabled") is not None:
                    # See SUBMIT_DISABLED_RETRY_ATTEMPTS above: give a slow-
                    # mounting reCAPTCHA widget (or the button itself) a few
                    # more beats before giving up on this step.
                    still_disabled = True
                    for _ in range(SUBMIT_DISABLED_RETRY_ATTEMPTS):
                        await page.wait_for_timeout(SUBMIT_DISABLED_RETRY_MS)
                        challenge = await detect_challenge(page)
                        if challenge is not None:
                            if pause_on_manual:
                                return await _resolve_pause(
                                    page, f"challenge detected: {challenge.value}", challenge.value
                                )
                            raise ChallengeDetected(challenge)
                        if await submit_button.first.get_attribute("disabled") is None:
                            still_disabled = False
                            break

                    if still_disabled:
                        if pause_on_manual:
                            return await _resolve_pause(
                                page,
                                "submit button stayed disabled with no challenge detected",
                                "unknown_challenge",
                            )
                        return {
                            "status": "manual_action_required",
                            "reason": "submit button stayed disabled with no challenge detected",
                        }

                await submit_button.first.click()
                return {"status": "submitted"}

            if "resume-selection" in url:
                await _handle_resume_selection(page, resume_path)
                await page.wait_for_timeout(STEP_SETTLE_MS)
                continue

            if "questions-module" in url:
                # Confirmed via a real trial: employer-custom screening
                # questions (arbitrary text, radio groups + free-text
                # inputs), required before Continue does anything.
                # answer_questions() has its own blocklist gate for
                # consequential/legal-adjacent questions (work authorization,
                # sponsorship, salary, etc.) - it returns False and touches
                # nothing if any question matches, or if it can't confidently
                # match an LLM answer back to a real option.
                answered = await answer_questions(page, profile)
                if not answered:
                    if pause_on_manual:
                        return await _resolve_pause(
                            page, f"screening questions need a human at {url}", "unknown_challenge"
                        )
                    return {
                        "status": "manual_action_required",
                        "reason": f"screening questions need a human at {url}",
                    }
                advanced = False
                for label in GENERIC_CONTINUE_LABELS:
                    if await _click_visible(page, label):
                        advanced = True
                        break
                if not advanced:
                    if pause_on_manual:
                        return await _resolve_pause(
                            page,
                            f"answered questions but found no way to advance at {url}",
                            "unknown_challenge",
                        )
                    return {
                        "status": "failed",
                        "reason": f"answered questions but found no way to advance at {url}",
                    }
                await page.wait_for_timeout(STEP_SETTLE_MS)
                continue

            advanced = await _handle_generic_step(page, profile)
            if not advanced:
                if pause_on_manual:
                    return await _resolve_pause(
                        page, f"no actionable step found at {url}", "unknown_challenge"
                    )
                return {"status": "failed", "reason": f"no actionable step found at {url}"}
            await page.wait_for_timeout(STEP_SETTLE_MS)

        if pause_on_manual:
            return await _resolve_pause(
                page, "exceeded max steps without reaching submission", "unknown_challenge"
            )
        return {"status": "failed", "reason": "exceeded max steps without reaching submission"}
