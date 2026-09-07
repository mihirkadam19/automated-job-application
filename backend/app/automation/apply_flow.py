import asyncio

from playwright.async_api import BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation import browser_manager
from app.automation.challenge_detection import ChallengeDetected, CheckpointType, detect_challenge
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

# Confirmed via a real trial: right after launch_subprocess_cdp_context
# navigates to the job page, Cloudflare's check can still be resolving (or
# waiting on a human to clear it) for several seconds - a single instant
# look for the Apply button was concluding "no native Apply flow" before
# ever giving the page a chance to actually render, even though the button
# was there moments later. Only waits when headed - no point polling
# minutes with nobody there to help clear anything.
APPLY_BUTTON_WAIT_TIMEOUT_SECONDS = 180
APPLY_BUTTON_POLL_INTERVAL_SECONDS = 3

# Confirmed via a real trial that a detected challenge needs its own bounded
# wait, separate from pause_on_manual entirely: a human watching a headed
# run can often clear Cloudflare's gate in seconds (sometimes it clears on
# its own with no action at all), and the automation should just RESUME
# once it does - not immediately give up, and not hang around waiting for
# the browser to be closed either (that full hand-off is pause_on_manual's
# job, reserved for resume_manually's deliberate "let a human finish this"
# case). This is what makes a normal automated run actually benefit from a
# human watching a headed window, instead of failing the instant anything
# shows up.
CHALLENGE_CLEAR_TIMEOUT_SECONDS = 120
CHALLENGE_CLEAR_POLL_SECONDS = 3

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


async def _await_challenge_clear(
    page: Page, challenge: CheckpointType, headless: bool
) -> CheckpointType | None:
    """Given a challenge just detected, waits (bounded, only if headed -
    someone might be watching) for it to clear, re-checking periodically,
    then returns None so the caller can just carry on with the step it was
    already on. Returns the last-seen challenge unchanged if it never
    cleared in time, or immediately if headless (nobody's there for a wait
    to matter). This is deliberately separate from pause_on_manual - that
    flag controls what happens once we truly give up, not whether we give
    this a chance to resolve itself first."""
    if headless:
        return challenge
    elapsed = 0
    while challenge is not None and elapsed < CHALLENGE_CLEAR_TIMEOUT_SECONDS:
        await page.wait_for_timeout(CHALLENGE_CLEAR_POLL_SECONDS * 1000)
        elapsed += CHALLENGE_CLEAR_POLL_SECONDS
        challenge = await detect_challenge(page)
    return challenge


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


async def _drive_apply_flow(
    context: BrowserContext,
    job_url: str,
    profile: dict,
    resume_path: str | None,
    headless: bool,
    pause_on_manual: bool,
) -> dict:
    """The actual step-by-step wizard logic, factored out of apply_to_job so
    it can run against launch_subprocess_cdp_context's browser. headless
    controls whether a stalled step gets a bounded wait-for-clear chance
    before giving up (see _await_challenge_clear/APPLY_BUTTON_WAIT above);
    pause_on_manual controls only what happens once we truly give up on a
    step (see apply_to_job's docstring)."""
    page = await context.new_page()
    await page.goto(job_url, timeout=30000)
    await page.wait_for_timeout(2000)

    # Check for a challenge FIRST, before drawing any conclusion about the
    # page's actual content - confirmed via a real trial that checking for
    # the Apply button first and only reactively checking for a challenge
    # once that came up empty meant a challenge that hadn't rendered yet
    # within our flat settle delay got misdiagnosed as "no native Apply
    # flow" instead of being given any chance to clear.
    challenge = await detect_challenge(page)
    if challenge is not None:
        challenge = await _await_challenge_clear(page, challenge, headless)
    if challenge is not None:
        if pause_on_manual:
            return await _resolve_pause(
                page, f"challenge detected: {challenge.value}", challenge.value
            )
        raise ChallengeDetected(challenge)

    apply_button = page.get_by_role("button", name="Apply with Indeed").locator("visible=true")
    if await apply_button.count() == 0 and not headless:
        # See APPLY_BUTTON_WAIT_TIMEOUT_SECONDS above - give the page time
        # to actually settle before concluding there's no apply flow here.
        elapsed = 0
        while await apply_button.count() == 0 and elapsed < APPLY_BUTTON_WAIT_TIMEOUT_SECONDS:
            await page.wait_for_timeout(APPLY_BUTTON_POLL_INTERVAL_SECONDS * 1000)
            elapsed += APPLY_BUTTON_POLL_INTERVAL_SECONDS
            apply_button = page.get_by_role("button", name="Apply with Indeed").locator("visible=true")
            # A challenge can also appear mid-wait, not just at the start.
            challenge = await detect_challenge(page)
            if challenge is not None:
                if pause_on_manual:
                    return await _resolve_pause(
                        page, f"challenge detected: {challenge.value}", challenge.value
                    )
                raise ChallengeDetected(challenge)

    if await apply_button.count() == 0:
        if pause_on_manual:
            return await _resolve_pause(
                page, "no native Indeed Apply flow for this job", "unknown_challenge"
            )
        return {"status": "unsupported", "reason": "no native Indeed Apply flow for this job"}

    # Confirmed via a real trial: clicking "Apply with Indeed" can open the
    # actual SmartApply wizard in a NEW tab/popup rather than navigating the
    # current page - the original tab just bounces back to the job posting
    # (with "&from=iaBackPress" appended) while the real flow happens
    # elsewhere. Watch for that popup around the click and switch to
    # driving it instead of the now-stale original page.
    print(f"[apply_flow] found Apply button, count={await apply_button.count()}, url before click={page.url}", flush=True)
    try:
        async with context.expect_page(timeout=5000) as new_page_info:
            await apply_button.first.click()
            print("[apply_flow] click() call returned", flush=True)
        popup = await new_page_info.value
        await popup.wait_for_load_state()
        page = popup
        print(f"[apply_flow] popup detected, switched to it, url={page.url}", flush=True)
    except PlaywrightTimeoutError:
        print(f"[apply_flow] no popup within 5s, url after click={page.url}", flush=True)

    await page.wait_for_timeout(STEP_SETTLE_MS)
    print(f"[apply_flow] after settle, url={page.url}, context.pages={[p.url for p in context.pages]}", flush=True)

    for _ in range(MAX_STEPS):
        challenge = await detect_challenge(page)
        if challenge is not None:
            challenge = await _await_challenge_clear(page, challenge, headless)
        if challenge is not None:
            if pause_on_manual:
                return await _resolve_pause(
                    page, f"challenge detected: {challenge.value}", challenge.value
                )
            raise ChallengeDetected(challenge)

        url = page.url

        if "review-module" in url:
            await page.wait_for_timeout(STEP_SETTLE_MS)

            # Re-check right before the highest-stakes action: a challenge
            # can appear in the gap between this iteration's top-of-loop
            # check and now - confirmed via a real trial where the submit
            # click timed out on a disabled button instead of a challenge
            # ever being raised.
            challenge = await detect_challenge(page)
            if challenge is not None:
                challenge = await _await_challenge_clear(page, challenge, headless)
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
                        challenge = await _await_challenge_clear(page, challenge, headless)
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
            # questions (arbitrary text, radio groups + free-text inputs),
            # required before Continue does anything. answer_questions()
            # has its own blocklist gate for consequential/legal-adjacent
            # questions (work authorization, sponsorship, salary, etc.) - it
            # returns False and touches nothing if any question matches, or
            # if it can't confidently match an LLM answer back to a real
            # option.
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


async def apply_to_job(
    storage_state: dict,
    job_url: str,
    profile: dict,
    resume_path: str | None = None,
    headless: bool = True,
    pause_on_manual: bool = False,
    browser_mode: str = browser_manager.DEFAULT_BROWSER_MODE,
) -> dict:
    """Drive Indeed's native apply wizard using an already-authenticated
    session. Only supports jobs with a native "Apply with Indeed" flow -
    "Apply on company site" jobs redirect to an arbitrary third-party site
    and are reported as unsupported rather than attempted. Raises
    ChallengeDetected if Indeed shows a CAPTCHA/verification that never
    clears, unless pause_on_manual is set (see below).

    browser_mode picks how the browser gets launched (see
    browser_manager.launch) - defaults to "os_chrome" since that's the only
    one confirmed to get past Cloudflare's automation detection this
    session, with zero exceptions, while Playwright's own chromium.launch()
    ("playwright") got flagged every single time. "playwright" is kept
    available for a different account/environment/day where that isn't an
    issue, since it's simpler and faster (no subprocess+CDP dance).

    headless and pause_on_manual are deliberately separate concerns,
    confirmed necessary via a real trial where conflating them made every
    single automated headed run hang waiting for the browser to be closed,
    even after a challenge had already cleared on its own:
      - headless controls whether a stalled step gets a bounded wait for
        the stall to clear before giving up at all (a human watching a
        headed run can often clear Cloudflare's gate in seconds, sometimes
        it clears with no action needed) - once clear, the automation just
        resumes the wizard on its own. Never waits when headless=True,
        since nobody's there for it to matter.
      - pause_on_manual controls only what happens once a step is truly,
        finally given up on: if True, the browser stays open and this
        function blocks until a human closes it, so they can take over
        mid-wizard by hand (resume_manually's use case); if False, the
        stall is reported immediately (raised or returned) with no further
        waiting - the normal automated path.

    An earlier trial found the final submit button stuck disabled in
    headless mode and enabled in headed mode, which looked like a
    headless-specific gate - but a later trial showed the same "disabled"
    outcome in headed mode too, on a run that turned out to have hit a real
    reCAPTCHA checkbox challenge_detection wasn't catching yet (now fixed).
    So headed was never the actual fix; it was a missed CAPTCHA. headless
    defaults to True here to match job_search.py, with the caller free to
    force headed=False to give a human the chance to help clear something."""
    async with browser_manager.launch(browser_mode, headless=headless, storage_state=storage_state) as context:
        return await _drive_apply_flow(context, job_url, profile, resume_path, headless, pause_on_manual)
