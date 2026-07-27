"""Prediction model — one row per inference request."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    predicted_class: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    probs: Mapped[dict] = mapped_column(JSON, nullable=False)
    inference_ms: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped[User] = relationship(back_populates="predictions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Prediction id={self.id} label={self.label!r} conf={self.confidence:.3f}>"
