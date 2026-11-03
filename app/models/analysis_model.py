import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.article_model import Article
    from app.models.prompt_version_model import PromptVersion
    from app.models.validation_model import Validation


class Analysis(UUIDPrimaryKeyMixin, Base):
    """Avaliação da LLM para um artigo, sob uma versão de critérios e um modelo."""

    __tablename__ = "analyses"
    __table_args__ = (
        UniqueConstraint(
            "article_id", "prompt_version_id", "llm_model",
            name="uq_analyses_article_version_model",
        ),
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompt_versions.id"), index=True
    )
    llm_model: Mapped[str] = mapped_column(Text)
    scores: Mapped[dict] = mapped_column(JSONB)  # {"interesse_publico": 8, ...}
    justificativas: Mapped[dict | None] = mapped_column(JSONB)
    justificativa_geral: Mapped[str | None] = mapped_column(Text)
    enfoques: Mapped[list | None] = mapped_column(JSONB)
    score_final: Mapped[float | None] = mapped_column(Numeric(4, 2), index=True)
    recomendado: Mapped[bool | None] = mapped_column(Boolean)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    article: Mapped["Article"] = relationship(back_populates="analyses")
    prompt_version: Mapped["PromptVersion"] = relationship(back_populates="analyses")
    validations: Mapped[list["Validation"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )