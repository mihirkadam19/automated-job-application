from sqlalchemy.orm import Session

from app.automation import browser_manager, job_search
from app.automation.challenge_detection import ChallengeDetected
from app.automation.storage_state_crypto import decrypt_storage_state
from app.db.models import IndeedSession, SessionStatus


async def search(
    db: Session,
    session_id: str,
    query: str,
    location: str = "",
    limit: int = 10,
    headless: bool = True,
    browser_mode: str = browser_manager.DEFAULT_BROWSER_MODE,
) -> list[dict]:
    """Restores the session's login and runs a read-only Indeed search.
    Nothing about the search itself (query, results) is persisted - the
    session row is only touched if a challenge comes up, so a later call
    knows to re-validate/re-import before trying again. Raises
    ChallengeDetected (from job_search.search_jobs) unchanged - there's no
    Application/Checkpoint to attach it to here, so the api layer is
    responsible for turning that into a response."""
    session = db.get(IndeedSession, session_id)
    if session is None:
        raise LookupError(f"session {session_id} not found")
    if session.encrypted_storage_state is None:
        raise ValueError(f"session {session_id} has no captured login to search with")

    storage_state = decrypt_storage_state(session.encrypted_storage_state)

    try:
        return await job_search.search_jobs(
            storage_state, query, location, limit, headless, browser_mode
        )
    except ChallengeDetected:
        # A challenge here means the stored login itself likely needs
        # re-verifying, not just this one search retried - flag the session
        # the same way session_service.refresh does for a stale login,
        # rather than leaving it reporting active.
        session.status = SessionStatus.NEEDS_VERIFICATION
        db.commit()
        raise
