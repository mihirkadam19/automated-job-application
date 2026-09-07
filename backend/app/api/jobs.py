from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.automation import browser_manager
from app.automation.challenge_detection import ChallengeDetected
from app.db.base import get_db
from app.services import job_search_service

router = APIRouter(prefix="/jobs", tags=["jobs"])

# See app/api/applications.py's BrowserMode for what these mean - shared
# here since search also drives a real browser.
BrowserMode = Literal["playwright", "os_chrome"]


class JobSearchRequest(BaseModel):
    session_id: str
    query: str
    location: str = ""
    limit: int = 10
    headless: bool = True
    browser_mode: BrowserMode = browser_manager.DEFAULT_BROWSER_MODE


@router.post("/search")
async def search_jobs(payload: JobSearchRequest, db: Session = Depends(get_db)):
    try:
        jobs = await job_search_service.search(
            db,
            payload.session_id,
            payload.query,
            payload.location,
            payload.limit,
            payload.headless,
            payload.browser_mode,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="session not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ChallengeDetected as e:
        raise HTTPException(
            status_code=409,
            detail=f"challenge detected: {e.checkpoint_type.value}, session marked needs_verification",
        )
    return jobs
