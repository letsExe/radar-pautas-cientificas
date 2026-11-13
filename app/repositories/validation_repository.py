from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models import Analysis, Validation


class ValidationRepository:
    """Grava a validação humana. Não faz commit: quem chama decide a transação."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def analysis_exists(self, analysis_id: UUID) -> bool:
        return bool(self._session.scalar(select(exists().where(Analysis.id == analysis_id))))

    def find(self, analysis_id: UUID, reviewer_name: str) -> Validation | None:
        stmt = select(Validation).where(
            Validation.analysis_id == analysis_id,
            Validation.reviewer_name == reviewer_name,
        )
        return self._session.scalars(stmt).first()

    def save(self, analysis_id: UUID, reviewer_name: str, agrees: bool, comment: str | None) -> None:
        """Um revisor tem no máximo uma validação por análise: reenviar atualiza a anterior."""
        existing = self.find(analysis_id, reviewer_name)
        if existing:
            existing.agrees = agrees
            existing.comment = comment
            existing.validated_at = datetime.now(timezone.utc)
        else:
            self._session.add(
                Validation(
                    analysis_id=analysis_id,
                    reviewer_name=reviewer_name,
                    agrees=agrees,
                    comment=comment,
                )
            )
        self._session.flush()