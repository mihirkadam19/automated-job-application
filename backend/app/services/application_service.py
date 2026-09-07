from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.automation.apply_flow import apply_to_job
from app.automation.challenge_detection import ChallengeDetected
from app.automation.storage_state_crypto import decrypt_storage_state
from app.db.models import (
    Application,
    ApplicationStatus,
    Checkpoint,
    CheckpointStatus,
    CheckpointType,
    IndeedSession,
)

# Maps apply_to_job()'s result["status"] strings onto our own enum. "unsupported"
# (no native Indeed Apply flow) is treated as FAILED rather than a distinct
# status - from a tracking standpoint it's a terminal non-retryable outcome
# just like a real failure, and doesn't get its own DB status per the brief's
# scope (submitted / failed / manual_action_required / in-progress states).
_RESULT_STATUS_MAP = {
    "submitted": ApplicationStatus.SUBMITTED,
    "manual_action_required": ApplicationStatus.MANUAL_ACTION_REQUIRED,
    "failed": ApplicationStatus.FAILED,
    "unsupported": ApplicationStatus.FAILED,
}


def get_or_create_application(
    db: Session,
    session_id: str,
    job_url: str,
    job_title: str,
    company: str,
    external_job_id: str | None = None,
) -> Application:
    """Looks up the existing row for this (session, job) pair first - the
    unique constraint means a retry on the same job must reuse the row
    (bumping attempt_count via run_application) rather than ever inserting a
    duplicate. Only creates a fresh PENDING row the first time."""
    existing = (
        db.query(Application)
        .filter(Application.session_id == session_id, Application.job_url == job_url)
        .first()
    )
    if existing is not None:
        return existing

    application = Application(
        session_id=session_id,
        job_url=job_url,
        job_title=job_title,
        company=company,
        external_job_id=external_job_id,
        status=ApplicationStatus.PENDING,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


async def run_application(
    db: Session,
    application_id: str,
    profile: dict,
    resume_path: str | None = None,
    headless: bool = True,
) -> Application:
    """Drives apply_to_job for an already-created Application row and
    persists the outcome. profile is only ever passed through in-memory to
    the automation layer - never written to this row or anywhere else."""
    application = db.get(Application, application_id)
    if application is None:
        raise LookupError(f"application {application_id} not found")

    session = db.get(IndeedSession, application.session_id)
    if session is None or session.encrypted_storage_state is None:
        raise ValueError(f"session {application.session_id} has no captured login to apply with")

    storage_state = decrypt_storage_state(session.encrypted_storage_state)

    application.status = ApplicationStatus.IN_PROGRESS
    application.attempt_count += 1
    db.commit()

    try:
        result = await apply_to_job(
            storage_state, application.job_url, profile, resume_path, headless
        )
        application.status = _RESULT_STATUS_MAP.get(result["status"], ApplicationStatus.FAILED)
        application.last_error = result.get("reason")
        if application.status == ApplicationStatus.SUBMITTED:
            application.submitted_at = datetime.now(timezone.utc)
        elif application.status == ApplicationStatus.MANUAL_ACTION_REQUIRED:
            # apply_to_job can land here two ways: a raised ChallengeDetected
            # (handled below, with a real typed Checkpoint) or a plain
            # {"status": "manual_action_required"} dict for a stall it
            # couldn't classify as a specific challenge (e.g. a submit
            # button that stayed disabled with no challenge detected). That
            # second case used to leave no Checkpoint at all - record it as
            # UNKNOWN_CHALLENGE so it still shows up as something a human
            # needs to look at, not just a status flag with no queue entry.
            db.add(
                Checkpoint(
                    application_id=application.id,
                    type=CheckpointType.UNKNOWN_CHALLENGE,
                    status=CheckpointStatus.PENDING,
                )
            )
    except ChallengeDetected as e:
        checkpoint = Checkpoint(
            application_id=application.id,
            type=e.checkpoint_type,
            status=CheckpointStatus.PENDING,
        )
        db.add(checkpoint)
        application.status = ApplicationStatus.MANUAL_ACTION_REQUIRED
        application.last_error = f"challenge detected: {e.checkpoint_type.value}"
    except Exception as e:
        application.status = ApplicationStatus.FAILED
        application.last_error = str(e)

    db.commit()
    db.refresh(application)
    return application


def get_application(db: Session, application_id: str) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise LookupError(f"application {application_id} not found")
    return application


def list_applications(
    db: Session, session_id: str | None = None, status: str | None = None
) -> list[Application]:
    query = db.query(Application)
    if session_id is not None:
        query = query.filter(Application.session_id == session_id)
    if status is not None:
        try:
            status_enum = ApplicationStatus(status)
        except ValueError:
            raise ValueError(f"invalid status: {status}")
        query = query.filter(Application.status == status_enum)
    return query.order_by(Application.created_at.desc()).all()


async def resume_manually(
    db: Session, application_id: str, profile: dict, resume_path: str | None = None
) -> Application:
    """Re-drives the SAME automated flow as run_application (resume
    selection, LLM-answered screening questions, everything) in a real
    headed browser with the session's login restored - so the human isn't
    handed a blank job posting and made to redo work we can already do.
    apply_to_job's pause_on_manual mode makes it stop advancing and leave
    the browser open at exactly the point that needs a human (a challenge,
    an unanswerable question, a stuck submit button) rather than raising/
    returning immediately. Only meant for applications that already stalled
    on something we won't touch ourselves. Blocks until the human closes the
    browser; on close, checks the last URL seen and marks the application
    SUBMITTED if it reached Indeed's real post-apply confirmation page."""
    application = db.get(Application, application_id)
    if application is None:
        raise LookupError(f"application {application_id} not found")
    if application.status != ApplicationStatus.MANUAL_ACTION_REQUIRED:
        raise ValueError(
            f"application {application_id} is {application.status.value}, "
            "not manual_action_required - nothing to resume"
        )

    session = db.get(IndeedSession, application.session_id)
    if session is None or session.encrypted_storage_state is None:
        raise ValueError(f"session {application.session_id} has no captured login to restore")

    storage_state = decrypt_storage_state(session.encrypted_storage_state)

    application.status = ApplicationStatus.IN_PROGRESS
    application.attempt_count += 1
    db.commit()

    result = await apply_to_job(
        storage_state,
        application.job_url,
        profile,
        resume_path,
        headless=False,
        pause_on_manual=True,
    )

    application.status = _RESULT_STATUS_MAP.get(result["status"], ApplicationStatus.FAILED)
    application.last_error = result.get("reason")

    if application.status == ApplicationStatus.SUBMITTED:
        application.submitted_at = datetime.now(timezone.utc)
        application.last_error = None
        # Whatever was previously blocking this application is moot now -
        # close out any still-pending checkpoints on it.
        for checkpoint in db.query(Checkpoint).filter(
            Checkpoint.application_id == application.id,
            Checkpoint.status == CheckpointStatus.PENDING,
        ):
            checkpoint.status = CheckpointStatus.RESOLVED
            checkpoint.resolved_at = datetime.now(timezone.utc)
    elif "checkpoint_type" in result:
        # Still stalled, possibly on something different than last time -
        # record it, but don't duplicate an identical pending checkpoint.
        checkpoint_type = CheckpointType(result["checkpoint_type"])
        already_pending = (
            db.query(Checkpoint)
            .filter(
                Checkpoint.application_id == application.id,
                Checkpoint.status == CheckpointStatus.PENDING,
                Checkpoint.type == checkpoint_type,
            )
            .first()
        )
        if already_pending is None:
            db.add(
                Checkpoint(
                    application_id=application.id,
                    type=checkpoint_type,
                    status=CheckpointStatus.PENDING,
                )
            )

    db.commit()
    db.refresh(application)
    return application
