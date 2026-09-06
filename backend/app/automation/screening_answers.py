from anthropic import Anthropic
from playwright.async_api import Page

from app.config import get_settings

MODEL = "claude-sonnet-5"

_NOT_SENSITIVE = object()

TEXT_FIELD_SELECTOR = (
    "input[type=number], input[type=text], input[type=email], input[type=tel], textarea"
)

# Confirmed via a real trial to be the actual root cause of every "our
# answer got silently reverted" case seen on this form (radios and
# checkboxes alike) - not Indeed re-applying saved answers as first
# suspected. React patches the `checked` setter at the DOM *instance*
# level to track controlled-input changes; writing `el.checked = true`
# goes through that patched setter, which updates React's internal tracker
# too, so when the dispatched 'change' event fires, React's tracker sees
# "no real change" and never re-renders its own state - any later,
# unrelated re-render then snaps the checkbox/radio back to React's actual
# (unchanged) state. Calling the *prototype's* native setter bypasses
# React's instance-level patch, leaving the tracker out of sync so the
# dispatched event triggers a real update.
_SET_CHECKED_JS = (
    "el => { "
    "const proto = Object.getPrototypeOf(el); "
    "const setter = Object.getOwnPropertyDescriptor(proto, 'checked').set; "
    "setter.call(el, true); "
    "el.dispatchEvent(new Event('input', { bubbles: true })); "
    "el.dispatchEvent(new Event('change', { bubbles: true })); }"
)


def _format_value(value) -> str:
    """Turns a raw profile fact into literal answer text - one generalized
    rule, not a formatter per category. A bool becomes Yes/No (matches how
    these forms render boolean questions); anything else (a number, a
    string) is used as-is. A plain number like 80000 already satisfies a
    numeric field's validation and reads fine as plain text too, so no
    per-field-type formatting is needed here at all."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


# Consequential / legal-adjacent categories - never guessed by the LLM.
# Answered directly from explicit profile fields (the candidate's own
# stated facts) if present; if the matching field is missing, falls back
# to manual_action_required rather than guessing. Resolvers return the raw
# fact (bool/number/string) - _format_value turns it into answer text.
SENSITIVE_RESOLVERS = {
    ("authorized to work", "work authorization"): lambda p: p.get("work_authorized"),
    ("sponsorship", "sponsor"): lambda p: p.get("requires_sponsorship"),
    ("security clearance", "clearance"): lambda p: p.get("has_security_clearance"),
    ("felony", "convicted"): lambda p: p.get("felony_conviction"),
    ("professional license", "licensure"): lambda p: p.get("has_professional_license"),
    ("visa",): lambda p: p.get("visa_status"),
    ("salary", "compensation expectation", "pay expectation"): lambda p: p.get(
        "desired_salary"
    ),
}

# Sensitive, but with no profile field to answer from at all - always falls
# back to manual_action_required.
UNRESOLVED_SENSITIVE_KEYWORDS = ("background check",)

# EEO/demographic questions (race, gender, veteran/disability status) are
# sensitive in a different way than the categories above: they're about
# protected personal identity, not verifiable facts, and are never guessed
# by the LLM either. These almost always include a "decline to self-
# identify" option specifically because answering is voluntary - always
# select that option when present; fall back to manual otherwise.
DEMOGRAPHIC_KEYWORDS = (
    "race",
    "ethnicity",
    "gender",
    "veteran",
    "disability",
    "sexual orientation",
    "demographic",
)

DECLINE_OPTION_MARKERS = (
    "decline",
    "prefer not",
    "don't wish",
    "do not wish",
    "not disclose",
    "not to disclose",
    "rather not",
)


def _decline_option_text(question: dict) -> str | None:
    if question["type"] != "radio":
        return None
    for option in question["options"]:
        lowered = option["text"].strip().lower()
        if any(marker in lowered for marker in DECLINE_OPTION_MARKERS):
            return option["text"]
    return None


def _sensitive_raw_value(question: dict, profile: dict):
    """Returns the raw profile fact (or literal decline-option text for
    demographic questions) if this question maps to a sensitive category
    with an answer available; None if it's sensitive but unanswerable
    (caller should abort to manual); or _NOT_SENSITIVE if this isn't a
    sensitive category at all (caller should use the LLM)."""
    lowered = question["text"].lower()

    if any(keyword in lowered for keyword in DEMOGRAPHIC_KEYWORDS):
        return _decline_option_text(question)

    for keywords, resolver in SENSITIVE_RESOLVERS.items():
        if any(keyword in lowered for keyword in keywords):
            value = resolver(profile)
            return value if value is not None else None
    if any(keyword in lowered for keyword in UNRESOLVED_SENSITIVE_KEYWORDS):
        return None
    return _NOT_SENSITIVE


def _client() -> Anthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    return Anthropic(api_key=settings.anthropic_api_key)


async def _field_metadata(field) -> dict:
    """Real attributes of the actual input element - fed to the LLM so it
    adapts its answer to whatever format the field genuinely expects
    (number, short text, etc.) instead of us hardcoding field-type
    branches. Confirmed via a real trial that filling a numeric field with
    a sentence gets silently rejected, blocking the form from advancing."""
    tag = await field.evaluate("el => el.tagName.toLowerCase()")
    return {
        "tag": tag,
        "type": await field.get_attribute("type"),
        "placeholder": await field.get_attribute("placeholder"),
        "min": await field.get_attribute("min"),
        "max": await field.get_attribute("max"),
        "step": await field.get_attribute("step"),
        "pattern": await field.get_attribute("pattern"),
        "maxlength": await field.get_attribute("maxlength"),
    }


async def _extract_questions(page: Page) -> list[dict]:
    blocks = page.locator("div[id^='q_']")
    count = await blocks.count()
    questions = []
    for i in range(count):
        block = blocks.nth(i)
        label_el = block.locator("[data-testid$='-label']").first
        if await label_el.count() == 0:
            continue
        text = (await label_el.inner_text()).strip()

        radios = block.locator("input[type=radio]")
        radio_count = await radios.count()
        if radio_count > 0:
            options = []
            for j in range(radio_count):
                radio = radios.nth(j)
                value = await radio.get_attribute("value")
                option_label = block.locator(f"label:has(input[value='{value}'])").first
                option_text = (
                    (await option_label.inner_text()).strip()
                    if await option_label.count() > 0
                    else value
                )
                options.append({"value": value, "text": option_text})
            questions.append({"index": i, "type": "radio", "text": text, "options": options})
            continue

        text_field = block.locator(TEXT_FIELD_SELECTOR)
        if await text_field.count() > 0:
            field_meta = await _field_metadata(text_field.first)
            questions.append(
                {"index": i, "type": "text", "text": text, "field_meta": field_meta}
            )

    return questions


def _ask_llm(question: dict, profile: dict) -> str:
    client = _client()
    if question["type"] == "radio":
        options_text = "\n".join(f"- {o['text']}" for o in question["options"])
        prompt = (
            f"Candidate profile: {profile}\n\n"
            f"Job application screening question: {question['text']}\n"
            f"Options:\n{options_text}\n\n"
            "Reply with ONLY the exact text of the single best matching option, "
            "nothing else - no punctuation, no explanation."
        )
    else:
        prompt = (
            f"Candidate profile: {profile}\n\n"
            f"Job application screening question: {question['text']}\n\n"
            f"The answer will be typed into an input field with these real "
            f"HTML attributes: {question['field_meta']}. Adapt your answer to "
            "whatever format this field actually expects - e.g. a bare "
            "number with no words or units for a numeric field, a short "
            "value for a small text field, or a fuller sentence for a "
            "general text field. Reply with ONLY the answer itself, nothing "
            "else - no explanation, no restating the question."
        )
    # Confirmed via real calls: this model can emit a ThinkingBlock before
    # the final text, and occasionally (intermittently - not tied to any
    # specific prompt content, not reproducible on retry with the same
    # input) returns no text block at all. Retry a couple of times before
    # giving up rather than crashing the whole apply attempt over it.
    last_error: Exception | None = None
    for _ in range(3):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text_block = next((block for block in response.content if block.type == "text"), None)
        if text_block is not None:
            return text_block.text.strip()
        last_error = RuntimeError("no text block in LLM response")
    raise last_error


# Standard "I agree to the privacy notice / terms" consent gates - not a
# real choice (declining just means you can't submit at all), functionally
# equivalent to what already happens implicitly when submitting any
# application (the final review page's own "by submitting you agree to
# terms..." disclaimer). Confirmed via a real trial: Indeed's demographic-
# questions page includes this consent checkbox with the full sentence in
# the fieldset's <legend>, not the checkbox's own <label> (just "Agree").
CONSENT_KEYWORDS = ("agree", "declare", "consent", "acknowledge", "privacy notice", "terms")


async def _checkbox_label_text(checkbox) -> str:
    checkbox_id = await checkbox.get_attribute("id")
    if checkbox_id:
        label = checkbox.page.locator(f"label[for='{checkbox_id}']")
        if await label.count() > 0:
            direct = (await label.first.inner_text()).strip()
            if direct and direct.lower() != "agree":
                return direct
    legend = checkbox.locator("xpath=ancestor::fieldset[1]//legend").first
    if await legend.count() > 0:
        return (await legend.inner_text()).strip()
    return ""


async def _check_consent_checkboxes(page: Page) -> bool:
    """Checks required, unchecked checkboxes whose associated text reads
    like a standard consent/agreement gate. Returns False (nothing further
    touched) the moment a checkbox doesn't match consent language - callers
    should fall back to manual rather than guess what it actually is."""
    async def _check(checkbox) -> None:
        # A real Playwright click is a genuine, trusted browser event -
        # React handles it exactly like an actual user click, no fighting
        # with its internal tracker needed. Only fall back to the JS
        # workaround if the checkbox can't be clicked normally (hidden /
        # off-viewport, as with the resume-selection radio elsewhere).
        try:
            await checkbox.click(timeout=3000)
        except Exception:
            await checkbox.evaluate(_SET_CHECKED_JS)

    checkboxes = page.locator("input[type=checkbox]")
    count = await checkboxes.count()
    consent_checkboxes = []
    for i in range(count):
        checkbox = checkboxes.nth(i)
        if await checkbox.is_checked():
            continue
        label_text = (await _checkbox_label_text(checkbox)).lower()
        if not any(keyword in label_text for keyword in CONSENT_KEYWORDS):
            return False
        await _check(checkbox)
        consent_checkboxes.append(checkbox)

    # Reverify and reapply once more right before returning: same revert
    # behavior confirmed for radio answers elsewhere on this site (likely
    # Indeed re-running some validation/hydration effect shortly after) was
    # also confirmed here via a real trial - a checkbox we just checked
    # showed unchecked again moments later, blocking the advance button
    # with a "Choose an option to continue" error.
    for checkbox in consent_checkboxes:
        if not await checkbox.is_checked():
            await _check(checkbox)

    return True


async def answer_questions(page: Page, profile: dict) -> bool:
    """Attempt to answer every screening question currently on the page.
    Sensitive categories (work authorization, visa, sponsorship, clearance,
    felony, professional license, salary) are answered directly from
    explicit profile fields, never guessed by the LLM. Other free-text
    fields are answered by the LLM, adapted to the field's real HTML
    attributes (numeric, short, etc.) via the prompt. Returns False (no
    fields touched) if any sensitive question has no matching profile
    field, or if an answer can't be confidently matched/filled - callers
    should fall back to manual_action_required."""
    questions = await _extract_questions(page)
    if not questions:
        # No recognized question blocks (div[id^='q_']) - confirmed via a
        # real trial: Indeed's demographic/consent page uses an entirely
        # different structure (ia-Questions-item class, no id="q_N",
        # checkboxes instead of radios). Handle the one pattern that's safe
        # to handle generically (consent checkboxes); anything else on such
        # a page falls back to manual rather than guessing.
        if await page.locator("input[type=checkbox]").count() > 0:
            return await _check_consent_checkboxes(page)
        unhandled = await page.locator("[data-testid$='-asterisk']").count()
        return unhandled == 0

    plan = []
    for q in questions:
        raw = _sensitive_raw_value(q, profile)
        if raw is None:
            return False
        plan.append((q, raw))

    blocks = page.locator("div[id^='q_']")
    fills = []  # (block, "radio", value) | (block, "text", answer_text)
    for q, raw in plan:
        answer_text = _format_value(raw) if raw is not _NOT_SENSITIVE else _ask_llm(q, profile)
        block = blocks.nth(q["index"])

        if q["type"] == "radio":
            matched = next(
                (
                    o
                    for o in q["options"]
                    if o["text"].strip().lower() == answer_text.strip().lower()
                ),
                None,
            )
            if matched is None:
                return False
            fills.append((block, "radio", matched["value"]))
        else:
            fills.append((block, "text", answer_text))

    async def _apply(block, kind, value) -> None:
        if kind == "radio":
            radio = block.locator(f"input[value='{value}']").first
            await radio.evaluate(_SET_CHECKED_JS)
        else:
            field = block.locator(TEXT_FIELD_SELECTOR).first
            await field.fill(value)

    for block, kind, value in fills:
        await _apply(block, kind, value)

    # Re-verify and reapply once more right before continuing: confirmed via
    # a real trial that a deterministic radio answer we set correctly can
    # get silently reverted later in this same page (most likely Indeed's
    # own "prefilled from your previous responses" logic re-applying a
    # saved answer asynchronously after ours). One reapply pass is a
    # pragmatic mitigation, not a root-cause fix.
    for block, kind, value in fills:
        if kind == "radio":
            radio = block.locator(f"input[value='{value}']").first
            if not await radio.is_checked():
                await _apply(block, kind, value)
        else:
            field = block.locator(TEXT_FIELD_SELECTOR).first
            if await field.input_value() != value:
                await _apply(block, kind, value)

    return True
