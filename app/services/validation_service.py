"""Regras da validação humana: quem pode validar, o que é aceito e como é gravado."""
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from app.repositories.validation_repository import ValidationRepository

MAX_COMMENT_CHARS = 2000


class ValidationError(ValueError):
    """Entrada recusada; a mensagem pode ser mostrada ao usuário."""


class ValidationService:
    def __init__(
        self, repository: ValidationRepository, allowed_reviewers: Sequence[str] = ()
    ) -> None:
        self._repository = repository
        self._allowed = tuple(allowed_reviewers)

    def submit(
        self, analysis_id: str, reviewer_name: str, agrees: bool, comment: str | None = None
    ) -> None:
        reviewer = " ".join((reviewer_name or "").split())
        if not reviewer:
            raise ValidationError("Informe o nome de quem está validando.")
        if self._allowed and reviewer not in self._allowed:
            raise ValidationError("Este nome não está na lista de revisores autorizados.")

        clean_comment = (comment or "").strip() or None
        if clean_comment and len(clean_comment) > MAX_COMMENT_CHARS:
            raise ValidationError(f"O comentário passa de {MAX_COMMENT_CHARS} caracteres.")

        try:
            analysis_uuid = UUID(str(analysis_id))
        except ValueError as exc:
            raise ValidationError("Identificador de análise inválido.") from exc

        try:
            if not self._repository.analysis_exists(analysis_uuid):
                raise ValidationError("Análise não encontrada.")
            self._repository.save(analysis_uuid, reviewer, bool(agrees), clean_comment)
        except SQLAlchemyError as exc:
            raise ValidationError("Não foi possível salvar agora. Tente de novo.") from exc