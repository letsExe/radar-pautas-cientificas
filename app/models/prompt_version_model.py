from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis_model import Analysis


class PromptVersion(UUIDPrimaryKeyMixin, Base):
    """Cada versão dos critérios de noticiabilidade (criterios.yaml)."""

    __tablename__ = "prompt_versions"

    config_hash: Mapped[str] = mapped_column(Text, unique=True)  # identifica a versão pelo conteúdo
    version_label: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSONB)  # cópia completa dos critérios usados
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="prompt_version")