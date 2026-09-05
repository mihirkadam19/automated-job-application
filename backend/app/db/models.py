import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    NEEDS_VERIFICATION = "needs_verification"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    FAILED = "failed"
    MANUAL_ACTION_REQUIRED = "manual_action_required"


class CheckpointType(str, enum.Enum):
    SMS_CODE = "sms_code"
    EMAIL_CODE = "email_code"
    CAPTCHA = "captcha"
    UNKNOWN_CHALLENGE = "unknown_challenge"


class CheckpointStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class IndeedSession(Base):
    """A captured Indeed login session. Login itself is done manually by a
    human in a visible browser; this row only stores the resulting encrypted
    storage_state so it can be restored later without a browser running."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    account_email: Mapped[str] = mapped_column(String(255), index=True)
    encrypted_storage_state: Mapped[bytes | None] = mapped_column(LargeBinary)
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus), default=SessionStatus.NEEDS_VERIFICATION, nullable=False
    )
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("session_id", "job_url", name="uq_application_session_job"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    job_title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    job_url: Mapped[str] = mapped_column(Text)
    external_job_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False, index=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["IndeedSession"] = relationship(back_populates="applications")
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class Checkpoint(Base):
    """A pause point raised by OUR automation (session refresh, job search, or
    the apply flow) hitting a challenge it can't and shouldn't solve itself.
    Never created for the login step, since login is entirely manual already."""

    __tablename__ = "checkpoints"
    __table_args__ = (
        CheckConstraint(
            "(session_id IS NOT NULL AND application_id IS NULL) OR "
            "(session_id IS NULL AND application_id IS NOT NULL)",
            name="ck_checkpoint_exactly_one_parent",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[str | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[CheckpointType] = mapped_column(SAEnum(CheckpointType), nullable=False)
    status: Mapped[CheckpointStatus] = mapped_column(
        SAEnum(CheckpointStatus), default=CheckpointStatus.PENDING, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    session: Mapped["IndeedSession | None"] = relationship(back_populates="checkpoints")
    application: Mapped["Application | None"] = relationship(back_populates="checkpoints")
