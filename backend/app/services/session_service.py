from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import IndeedSession, SessionStatus
from app.automation.browser_manager import launch_context
from app.automation.login_capture import ACCOUNT_URL, capture_login_session, looks_logged_in
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


async def start_capture(db: Session) -> IndeedSession:
    session = IndeedSession()
    db.add(session)
    db.commit()
    db.refresh(session)

    storage_state = await capture_login_session()

    if storage_state is not None:
        session.encrypted_storage_state = encrypt_storage_state(storage_state)
        session.status = SessionStatus.ACTIVE
        session.last_validated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)
    return session


def import_session(db: Session, storage_state: dict | list) -> IndeedSession:
    """Fallback to start_capture, for when Cloudflare's bot-management has
    escalated against the automated browser itself (confirmed via a real
    trial: a persistent, real on-disk Chrome profile still got blocked
    identically to a fresh one, isolating the cause to Playwright's CDP
    attachment rather than IP/profile freshness - not something a launch
    flag can fix). The human logs into Indeed in their own regular browser
    (already proven to pass), exports the resulting cookies, and we store
    them directly - zero automation ever touches the login page in this
    path, which is arguably even more "manual login only" than the
    browser-capture flow. No live validation against Indeed is attempted
    here on purpose: doing so would use the same automated browser that's
    the whole reason this path exists, and could misreport a good cookie
    export as bad. Downstream operations (job_search, apply_flow) will
    naturally surface a bad import the same way they'd surface any other
    stale session."""
    normalized = _normalize_storage_state(storage_state)

    session = IndeedSession(
        encrypted_storage_state=encrypt_storage_state(normalized),
        status=SessionStatus.ACTIVE,
        last_validated_at=datetime.now(timezone.utc),
    )
    db.add(session)
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


async def refresh(db: Session, session_id: str) -> IndeedSession:
    session = db.get(IndeedSession, session_id)
    if session is None:
        raise LookupError(f"session {session_id} not found")
    if session.encrypted_storage_state is None:
        raise ValueError(f"session {session_id} has no captured login to refresh")

    storage_state = decrypt_storage_state(session.encrypted_storage_state)

    async with launch_context(headless=True, storage_state=storage_state) as context:
        page = await context.new_page()
        await page.goto(ACCOUNT_URL)
        still_logged_in = looks_logged_in(page)

    session.last_validated_at = datetime.now(timezone.utc)
    session.status = SessionStatus.ACTIVE if still_logged_in else SessionStatus.NEEDS_VERIFICATION

    db.commit()
    db.refresh(session)
    return session
