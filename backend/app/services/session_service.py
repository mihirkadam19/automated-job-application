from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import IndeedSession, SessionStatus
from app.automation import browser_manager
from app.automation.login_capture import ACCOUNT_URL, looks_logged_in, open_login_window
from app.automation.storage_state_crypto import decrypt_storage_state, encrypt_storage_state

# Maps a cookie-export extension's sameSite values (Cookie-Editor and most
# others use Chrome's internal names) onto Playwright's expected enum.
# Anything unrecognized falls back to "Lax" - the modern browser default -
# rather than failing the whole import over one odd cookie.
_SAME_SITE_MAP = {
    "no_restriction": "None",
    "unspecified": "Lax",
    "lax": "Lax",
    "strict": "Strict",
    "none": "None",
}


def _normalize_storage_state(raw: dict | list) -> dict:
    """Accepts either Playwright's native storage_state shape
    ({"cookies": [...], "origins": [...]}) or a raw cookie array as exported
    by a browser extension like Cookie-Editor - fallback path is meant to be
    usable with whatever the human's browser's export tool actually
    produces, not just Playwright's own format. Never touches a browser to
    validate this - see import_session below for why."""
    if isinstance(raw, dict) and "cookies" in raw:
        return {"cookies": raw["cookies"], "origins": raw.get("origins", [])}

    if not isinstance(raw, list):
        raise ValueError(
            "storage_state must be either {'cookies': [...], 'origins': [...]} "
            "or a raw array of cookie objects"
        )

    cookies = []
    for c in raw:
        if "name" not in c or "value" not in c or "domain" not in c:
            raise ValueError(f"cookie missing name/value/domain: {c}")
        expires = -1
        if not c.get("session") and c.get("expirationDate") is not None:
            expires = int(c["expirationDate"])
        cookies.append(
            {
                "name": c["name"],
                "value": c["value"],
                "domain": c["domain"],
                "path": c.get("path", "/"),
                "expires": expires,
                "httpOnly": bool(c.get("httpOnly", False)),
                "secure": bool(c.get("secure", False)),
                "sameSite": _SAME_SITE_MAP.get(str(c.get("sameSite")).lower(), "Lax"),
            }
        )
    if not cookies:
        raise ValueError("no cookies found in import payload")
    return {"cookies": cookies, "origins": []}


def start_capture(db: Session) -> IndeedSession:
    """Creates a NEEDS_VERIFICATION session row and opens a genuinely plain,
    un-automated Chrome window at Indeed's login page (see
    login_capture.open_login_window for why - every Playwright-driven
    variant tried, regardless of browser engine/IP/profile, hit the same
    Cloudflare wall). Returns immediately: nothing is attached to that
    window, so there's no way to detect login completion or read cookies
    from it here. The human logs in normally, exports their cookies, and
    calls import_session with this row's id to actually activate it."""
    session = IndeedSession()
    db.add(session)
    db.commit()
    db.refresh(session)

    open_login_window()
    return session


def import_session(
    db: Session, storage_state: dict | list, session_id: str | None = None
) -> IndeedSession:
    """Populates a session's encrypted_storage_state from cookies the human
    exported out of their own real, already-logged-in browser (e.g. via the
    Cookie-Editor extension) - zero automation ever touches the login page
    in this path. Pass session_id to activate a row created by
    start_capture's plain-browser-window flow; omit it to create a
    standalone row from scratch. No live validation against Indeed is
    attempted here on purpose: doing so would use the same automated
    browser that's the whole reason this path exists, and could misreport a
    good cookie export as bad. Downstream operations (job_search,
    apply_flow) will naturally surface a bad import the same way they'd
    surface any other stale session."""
    normalized = _normalize_storage_state(storage_state)

    if session_id is not None:
        session = db.get(IndeedSession, session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
    else:
        session = IndeedSession()
        db.add(session)

    session.encrypted_storage_state = encrypt_storage_state(normalized)
    session.status = SessionStatus.ACTIVE
    session.last_validated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> IndeedSession:
    session = db.get(IndeedSession, session_id)
    if session is None:
        raise LookupError(f"session {session_id} not found")
    return session


def list_sessions(db: Session, status: str | None = None) -> list[IndeedSession]:
    query = db.query(IndeedSession)
    if status is not None:
        try:
            status_enum = SessionStatus(status)
        except ValueError:
            raise ValueError(f"invalid status: {status}")
        query = query.filter(IndeedSession.status == status_enum)
    return query.order_by(IndeedSession.created_at.desc()).all()


async def refresh(
    db: Session, session_id: str, browser_mode: str = browser_manager.DEFAULT_BROWSER_MODE
) -> IndeedSession:
    session = db.get(IndeedSession, session_id)
    if session is None:
        raise LookupError(f"session {session_id} not found")
    if session.encrypted_storage_state is None:
        raise ValueError(f"session {session_id} has no captured login to refresh")

    storage_state = decrypt_storage_state(session.encrypted_storage_state)

    async with browser_manager.launch(browser_mode, headless=True, storage_state=storage_state) as context:
        page = await context.new_page()
        await page.goto(ACCOUNT_URL)
        still_logged_in = looks_logged_in(page)

    session.last_validated_at = datetime.now(timezone.utc)
    session.status = SessionStatus.ACTIVE if still_logged_in else SessionStatus.NEEDS_VERIFICATION

    db.commit()
    db.refresh(session)
    return session
