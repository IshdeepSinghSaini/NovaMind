"""
document.py - Company documents and their pieces (chunks).

Tables:
- departments              : HR, IT, Finance, Product, General
- documents                : one row per uploaded file (its details / metadata)
- document_chunks          : the small text pieces of each document
                             (chunk.id is ALSO used as the ID inside ChromaDB)
- document_processing_logs : history of every processing attempt (success / failure)
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

PROCESSING_STATUSES = ("pending", "processing", "processed", "failed")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    documents: Mapped[list["Document"]] = relationship(back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'processed', 'failed')",
            name="ck_documents_processing_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Company's own ID written inside the document, e.g. "HR-002"
    doc_code: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # Safe random name used on disk (never trust the uploaded name)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # SHA-256 fingerprint of the file content -> blocks duplicate uploads
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf / docx / txt
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # bytes
    document_type: Mapped[Optional[str]] = mapped_column(String(50))  # Policy, Guide, Manual...
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    doc_created_date: Mapped[Optional[date]] = mapped_column(Date)

    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    access_level_id: Mapped[int] = mapped_column(ForeignKey("access_levels.id"), nullable=False)
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    processing_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    department: Mapped["Department"] = relationship(back_populates="documents")
    access_level: Mapped["AccessLevel"] = relationship()  # noqa: F821
    uploader: Mapped[Optional["User"]] = relationship()  # noqa: F821
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index"
    )
    processing_logs: Mapped[list["DocumentProcessingLog"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def to_dict(self, admin=False):
        """
        Safe version for API replies. Never includes the stored (disk) filename or the
        file hash. Admins additionally see who uploaded it.
        """
        data = {
            "id": self.id,
            "doc_code": self.doc_code,
            "title": self.title,
            "filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "document_type": self.document_type,
            "version": self.version,
            "doc_created_date": self.doc_created_date.isoformat() if self.doc_created_date else None,
            "department": self.department.name,
            "access_level": self.access_level.name,
            "processing_status": self.processing_status,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if admin:
            data["is_active"] = self.is_active
            data["uploaded_by"] = self.uploader.username if self.uploader else None
        return data

    def __repr__(self):
        return f"<Document {self.title}>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_chunk_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0, 1, 2, ...
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)  # PDFs
    section_reference: Mapped[Optional[str]] = mapped_column(String(255))  # headings (DOCX/TXT)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="chunks")

    def __repr__(self):
        return f"<Chunk doc={self.document_id} #{self.chunk_index}>"


class DocumentProcessingLog(Base):
    __tablename__ = "document_processing_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # processed / failed
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="processing_logs")
