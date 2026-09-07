from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.automation import browser_manager
from app.db.base import get_db
from app.db.models import Application
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])

# Sent on every request that drives a browser. "playwright" (Playwright's
# own chromium.launch()) is the default, since it's simpler and faster than
# "os_chrome" (plain subprocess-launched Chrome, connected to afterward via
# connect_over_cdp). Earlier live testing confirmed "os_chrome" is the only
# mode that reliably gets past Cloudflare's automation detection, so if a
# default request comes back with a captcha checkpoint, retry with
# browser_mode="os_chrome", or with the same mode but headless=False so a
# human can clear the challenge in the visible browser that opens.
BrowserMode = Literal["playwright", "os_chrome"]


class ApplicationCreateRequest(BaseModel):
    session_id: str
    job_url: str
    job_title: str
    company: str
    external_job_id: str | None = None
    profile: dict
    resume_path: str | None = None
    headless: bool = True
    browser_mode: BrowserMode = browser_manager.DEFAULT_BROWSER_MODE


class ApplicationResumeRequest(BaseModel):
    profile: dict
    resume_path: str | None = None
    browser_mode: BrowserMode = browser_manager.DEFAULT_BROWSER_MODE


def _serialize(application: Application) -> dict:
    return {
        "id": application.id,
        "session_id": application.session_id,
        "job_title": application.job_title,
        "company": application.company,
        "job_url": application.job_url,
        "external_job_id": application.external_job_id,
        "status": application.status.value,
        "attempt_count": application.attempt_count,
        "last_error": application.last_error,
        "submitted_at": application.submitted_at,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
    }


@router.post("", status_code=201)
async def create_application(payload: ApplicationCreateRequest, db: Session = Depends(get_db)):
    application = application_service.get_or_create_application(
        db,
        session_id=payload.session_id,
        job_url=payload.job_url,
        job_title=payload.job_title,
        company=payload.company,
        external_job_id=payload.external_job_id,
    )
    try:
        application = await application_service.run_application(
            db,
            application.id,
            profile=payload.profile,
            resume_path=payload.resume_path,
            headless=payload.headless,
            browser_mode=payload.browser_mode,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _serialize(application)


@router.get("")
def list_applications(
    session_id: str | None = None, status: str | None = None, db: Session = Depends(get_db)
):
    try:
        applications = application_service.list_applications(db, session_id, status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return [_serialize(a) for a in applications]


@router.get("/{application_id}")
def get_application(application_id: str, db: Session = Depends(get_db)):
    try:
        application = application_service.get_application(db, application_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="application not found")
    return _serialize(application)


@router.post("/{application_id}/resume")
async def resume_application(
    application_id: str, payload: ApplicationResumeRequest, db: Session = Depends(get_db)
):
    try:
        application = await application_service.resume_manually(
            db,
            application_id,
            profile=payload.profile,
            resume_path=payload.resume_path,
            browser_mode=payload.browser_mode,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="application not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _serialize(application)
