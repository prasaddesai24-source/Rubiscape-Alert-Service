"""
User model — stores registered users with hashed passwords and roles.
Supports RBAC: admin (full access) and viewer (read-only).
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """SQLAlchemy model for the 'users' table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(500), nullable=False)
    role = Column(String(20), nullable=False, default="viewer", comment="admin or viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
