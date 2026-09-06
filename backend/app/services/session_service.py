from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import IndeedSession, SessionStatus
from app.automation.browser_manager import launch_context
from app.automation.login_capture import ACCOUNT_URL, capture_login_session, looks_logged_in
from app.automation.storage_state_crypto import decrypt_storage_state, encrypt_storage_state


async def start_capture(db: Session, account_email: str) -> IndeedSession:
    session = IndeedSession(account_email=account_email)
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
