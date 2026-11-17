"""Persist only normalized invoice values; never retain uploaded PDFs or text."""

from sqlalchemy import JSON, Date, Integer, Numeric, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import UTC, datetime

from app.database.session import Base


class InvoiceRecord(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    billing_period: Mapped[str | None] = mapped_column(String(32))
    issued_on: Mapped[object | None] = mapped_column(Date)
    due_on: Mapped[object | None] = mapped_column(Date)
    consumption_m3: Mapped[object | None] = mapped_column(Numeric(12, 3))
    total_cop: Mapped[int | None] = mapped_column(Integer)
    fixed_charge_cop: Mapped[int | None] = mapped_column(Integer)
    variable_charge_cop: Mapped[int | None] = mapped_column(Integer)
    line_items: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    # Null rows are legacy local data and intentionally remain inaccessible.
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)


class UserRecord(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False)


class SessionRecord(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 of opaque cookie token
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
