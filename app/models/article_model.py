from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis_model import Analysis


class Article(UUIDPrimaryKeyMixin, Base):
    """Artigo coletado do OpenAlex (dado bruto, estável)."""

    __tablename__ = "articles"

    openalex_id: Mapped[str] = mapped_column(Text, unique=True)  # evita duplicar em novas coletas
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[list | None] = mapped_column(JSONB)
    publication_date: Mapped[date | None] = mapped_column(Date)
    source_name: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    work_type: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    topic: Mapped[str | None] = mapped_column(Text)
    research_field: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )