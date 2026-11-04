from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.criteria import CriteriaConfig
from app.models import PromptVersion


class PromptVersionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(self, config: CriteriaConfig) -> PromptVersion:
        """Devolve a versão dos critérios no banco; cria se o conteúdo ainda não foi registrado."""
        stmt = select(PromptVersion).where(PromptVersion.config_hash == config.content_hash)
        existing = self._session.scalar(stmt)
        if existing:
            return existing

        version = PromptVersion(
            config_hash=config.content_hash,
            version_label=config.version,
            config=config.raw,
        )
        self._session.add(version)
        self._session.flush()  # gera o id sem encerrar a transação
        return version