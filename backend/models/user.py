"""
user.py - Who can log in, and what they are allowed to see.

Tables:
- roles              : Admin, Employee, HR, Finance, IT
- access_levels      : Public, Employee, HR, Finance, IT  (labels put on documents)
- role_access_levels : which role may see which access level  (the RBAC rules)
- users              : the people who log in
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# A "link table": one row = "this role can see this access level".
# Many-to-many: one role sees many levels, one level is seen by many roles.
role_access_levels = Table(
    "role_access_levels",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("access_level_id", Integer, ForeignKey("access_levels.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(back_populates="role")
    access_levels: Mapped[list["AccessLevel"]] = relationship(
        secondary=role_access_levels, back_populates="roles"
    )

    def __repr__(self):
        return f"<Role {self.name}>"


class AccessLevel(Base):
    __tablename__ = "access_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    roles: Mapped[list["Role"]] = relationship(
        secondary=role_access_levels, back_populates="access_levels"
    )

    def __repr__(self):
        return f"<AccessLevel {self.name}>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Only the HASH is stored, never the real password
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    role: Mapped["Role"] = relationship(back_populates="users")

    def to_dict(self):
        """Safe version for API replies (no password hash!)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.name if self.role else None,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.email}>"
