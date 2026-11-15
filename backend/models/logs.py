"""
logs.py - Records of what happens in the system.

Tables:
- query_logs : every question asked (for analytics: how many, how fast, did it work)
- audit_logs : important actions (login, upload, delete, role change, blocked access)

Never store passwords or API keys in these tables.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# answered   = good answer from documents
# no_context = nothing relevant found -> "could not find sufficient information"
# error      = something broke (e.g. AI service down)
# blocked    = stopped by security (e.g. prompt injection, rate limit)
QUERY_STATUSES = ("answered", "no_context", "error", "blocked")


class QueryLog(Base):
    __tablename__ = "query_logs"
    __table_args__ = (
        CheckConstraint(
            "response_status IN ('answered', 'no_context', 'error', 'blocked')",
            name="ck_query_logs_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL")
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    top_score: Mapped[Optional[float]] = mapped_column(Float)
    response_status: Mapped[str] = mapped_column(String(20), nullable=False)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped[Optional["User"]] = relationship()  # noqa: F821


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL user = action by an unknown person (e.g. failed login with a wrong email)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. LOGIN_SUCCESS
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))  # e.g. document, user
    resource_id: Mapped[Optional[str]] = mapped_column(String(50))
    details: Mapped[Optional[dict]] = mapped_column(JSONB)  # extra info as JSON
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped[Optional["User"]] = relationship()  # noqa: F821
