"""Monta as dependências do sistema. É o único lugar que conhece todas as classes concretas."""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.criteria import load_criteria
from app.core.llm import get_llm_client
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.article_repository import ArticleRepository
from app.repositories.prompt_version_repository import PromptVersionRepository
from app.services.analysis_service import AnalysisService
from app.services.article_analyzer import ArticleAnalyzer
from app.services.collection_service import CollectionService
from app.services.pipeline_service import PipelineService


def build_pipeline(session: Session, provider: str | None = None) -> PipelineService:
    """Cria o pipeline pronto para uso, com todas as peças ligadas à mesma sessão."""
    config = load_criteria()
    version = PromptVersionRepository(session).get_or_create(config)
    session.commit()  # a versão dos critérios fica registrada mesmo se algo falhar depois

    analyzer = ArticleAnalyzer(get_llm_client(provider), config)
    analysis_service = AnalysisService(
        session,
        AnalysisRepository(session),
        analyzer,
        version.id,
        delay_seconds=settings.llm_delay_seconds,
    )
    collection_service = CollectionService(ArticleRepository(session))
    return PipelineService(
        session, collection_service, analysis_service, settings.require_institution_id()
    )