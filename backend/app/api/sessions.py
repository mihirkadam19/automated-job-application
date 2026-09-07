from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import IndeedSession
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionImportRequest(BaseModel):
    storage_state: dict | list
    session_id: str | None = None


def _serialize(session: IndeedSession) -> dict:
    return {
        "id": session.id,
        "status": session.status.value,
        "last_validated_at": session.last_validated_at,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@router.post("", status_code=201)
def create_session(db: Session = Depends(get_db)):
    session = session_service.start_capture(db)
    return _serialize(session)


@router.post("/import", status_code=201)
def import_session(payload: SessionImportRequest, db: Session = Depends(get_db)):
    try:
        session = session_service.import_session(db, payload.storage_state, payload.session_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="session not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _serialize(session)


@router.get("")
def list_sessions(status: str | None = None, db: Session = Depends(get_db)):
    try:
        sessions = session_service.list_sessions(db, status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return [_serialize(s) for s in sessions]


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    try:
        session = session_service.get_session(db, session_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="session not found")
    return _serialize(session)


@router.post("/{session_id}/refresh")
async def refresh_session(session_id: str, db: Session = Depends(get_db)):
    try:
        session = await session_service.refresh(db, session_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="session not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _serialize(session)
