from playwright.async_api import Page

from app.db.models import CheckpointType


class ChallengeDetected(Exception):
    """Raised by automation flows (job search, apply) when detect_challenge
    finds something a human needs to clear - never for login, which has no
    automated detection since it's entirely manual already."""

    def __init__(self, checkpoint_type: CheckpointType):
        self.checkpoint_type = checkpoint_type
        super().__init__(f"challenge detected: {checkpoint_type.value}")

# Confirmed via a real trial on Indeed's apply flow: a plain
# iframe[title*='recaptcha'] / iframe[src*='captcha'] check false-positives
# on Google's invisible anchor/badge frame, which is present on most pages
# for background scoring and is NOT an active challenge (src contains
# ".../recaptcha/enterprise/anchor", title is literally "reCAPTCHA", a tiny
# ~256x60 badge). A real active challenge escalates to Google's separate
# "bframe" (the image-grid challenge content frame).
#
# IMPORTANT (also confirmed via a real trial, on a plain search page with no
# active challenge at all): the bframe element is ALWAYS present in the DOM
# once reCAPTCHA loads, even in pure invisible mode - it's just kept
# non-visible (Playwright's is_visible() correctly reports False; a naive
# count()>0 check does NOT, since the element still occupies DOM space).
# So presence alone is meaningless here; visibility is the real signal.
# hCaptcha's equivalent challenge frame is an unverified guess by analogy,
# and presumed to need the same visibility check.
CAPTCHA_CHALLENGE_FRAME_SELECTORS = (
    "iframe[src*='bframe' i]",
    "iframe[title*='recaptcha challenge' i]",
    "iframe[title*='hcaptcha challenge' i]",
)

# Cloudflare Turnstile - unverified, never triggered in testing. Added
# because "challenges.cloudflare.com" appears in Indeed's real
# Content-Security-Policy header (confirmed via a real trial), meaning it's
# wired in even though we've never personally seen it fire. Selectors are
# Cloudflare's documented embed markers: the standard div.cf-turnstile
# container, its iframe (served from challenges.cloudflare.com, accessible
# title "Widget containing a Cloudflare security challenge"), and the
# classic full-page interstitial ("Just a moment...").
CLOUDFLARE_TURNSTILE_SELECTORS = (
    "div.cf-turnstile",
    "iframe[src*='challenges.cloudflare.com' i]",
    "iframe[title*='cloudflare security challenge' i]",
    "#challenge-running",
)

# Also confirmed via a real trial: the SAME anchor iframe (title="reCAPTCHA")
# can render either the harmless invisible v3 badge OR an actual "I'm not a
# robot" checkbox that must be clicked, escalating to the image-grid frame
# above if not trusted. Src/title alone can't tell these apart - both look
# identical from outside the frame. The real difference is inside it: the
# invisible badge's anchor frame has no checkbox at all, while an active
# challenge's anchor frame contains a real #recaptcha-anchor checkbox
# element. This is a best-effort fix based on one real occurrence - not
# re-verified against a second trial since the challenge appears
# stochastically and can't be reliably reproduced on demand.
async def _recaptcha_checkbox_present(page: Page) -> bool:
    for frame in page.frames:
        if "recaptcha" in frame.url and "anchor" in frame.url:
            try:
                if await frame.locator("#recaptcha-anchor").count() == 0:
                    continue
                # Guard against the same failure mode as bframe: the iframe
                # owning this frame could itself be hidden even though the
                # checkbox markup exists inside it.
                owner = await frame.frame_element()
                if await owner.is_visible():
                    return True
            except Exception:
                continue
    return False

# Confirmed shape from a real trial: an "Enter code" input on Indeed's
# verification screen (seen during the "We sent a code to <email>" flow).
OTP_INPUT_SELECTORS = (
    "input[autocomplete='one-time-code']",
    "input[name*='code' i]",
    "input[id*='otp' i]",
)


async def _any_visible(page: Page, selector: str) -> bool:
    locator = page.locator(selector)
    count = await locator.count()
    for i in range(count):
        if await locator.nth(i).is_visible():
            return True
    return False


async def detect_challenge(page: Page) -> CheckpointType | None:
    for selector in CAPTCHA_CHALLENGE_FRAME_SELECTORS:
        if await _any_visible(page, selector):
            return CheckpointType.CAPTCHA

    if await _recaptcha_checkbox_present(page):
        return CheckpointType.CAPTCHA

    for selector in CLOUDFLARE_TURNSTILE_SELECTORS:
        if await _any_visible(page, selector):
            return CheckpointType.CAPTCHA

    if "just a moment" in (await page.title()).lower():
        return CheckpointType.CAPTCHA

    # Confirmed via a real trial: a genuinely different page from
    # Cloudflare's Turnstile interstitial - Indeed's own basic
    # headless-Chromium bot-block (title exactly "Blocked - Indeed.com"),
    # seen when a launcher was missing --disable-blink-features=
    # AutomationControlled and a desktop Chrome User-Agent override for
    # headless mode (now fixed in browser_manager.py). Flagged as
    # UNKNOWN_CHALLENGE rather than CAPTCHA since there's nothing for a
    # human to click through here - it's an outright block, not a solvable
    # verification step - kept as a defensive fallback in case it recurs.
    if "blocked - indeed.com" in (await page.title()).lower():
        return CheckpointType.UNKNOWN_CHALLENGE

    otp_present = False
    for selector in OTP_INPUT_SELECTORS:
        if await page.locator(selector).count() > 0:
            otp_present = True
            break

    if not otp_present:
        return None

    body_text = (await page.locator("body").inner_text()).lower()
    if "email" in body_text:
        return CheckpointType.EMAIL_CODE
    if "phone" in body_text or "text message" in body_text or "sms" in body_text:
        return CheckpointType.SMS_CODE

    # Ambiguous wording - default to SMS_CODE, the more common case, since we
    # only have real confirmed data for the email variant so far.
    return CheckpointType.SMS_CODE
