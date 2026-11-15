"""
conversation.py - Chat history.

Tables:
- conversations     : one chat thread of a user ("Leave questions", ...)
- messages          : each question (user) and answer (assistant) inside a chat
- message_citations : which document chunks were used to build each answer
                      (also powers "most used documents" on the dashboard)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), default="New conversation", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("sender IN ('user', 'assistant')", name="ck_messages_sender"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    citations: Mapped[list["MessageCitation"]] = relationship(
        back_populates="message", cascade="all, delete-orphan", order_by="MessageCitation.rank"
    )


class MessageCitation(Base):
    __tablename__ = "message_citations"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SET NULL: if a document is deleted later, old chat answers still keep their text snapshot
    document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    chunk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("document_chunks.id", ondelete="SET NULL"))
    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = best match
    score: Mapped[Optional[float]] = mapped_column(Float)  # how relevant (0..1)
    # Snapshots, so the citation still makes sense even if the document changes
    document_title: Mapped[str] = mapped_column(String(255), nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    section_reference: Mapped[Optional[str]] = mapped_column(String(255))
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    message: Mapped["Message"] = relationship(back_populates="citations")
