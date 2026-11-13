"""Acesso a dados para a interface: abre a sessão, chama o serviço e guarda em cache.

Os resultados são objetos simples (schemas), por isso podem ficar em cache com segurança.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from app.core.config import settings
from app.core.database import session_scope
from app.repositories.ranking_repository import RankingRepository
from app.repositories.validation_repository import ValidationRepository
from app.schemas.ranking_schema import RankedArticle, RankingFilters, VersionView
from app.services.ranking_service import RankingService
from app.services.validation_service import ValidationService

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.article_repository import ArticleRepository
from app.schemas.overview_schema import Overview
from app.services.overview_service import OverviewService

CACHE_SECONDS = 300


def _service(session) -> RankingService:
    return RankingService(RankingRepository(session))


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def load_versions() -> list[VersionView]:
    with session_scope() as session:
        return _service(session).list_versions()


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def load_models(version_id: str) -> list[str]:
    with session_scope() as session:
        return _service(session).list_models(version_id)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def load_research_fields(version_id: str, model: str) -> list[str]:
    with session_scope() as session:
        return _service(session).list_research_fields(version_id, model)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Carregando ranking...")
def load_ranking(
    version_id: str,
    model: str,
    min_score: float,
    only_highlights: bool,
    only_unvalidated: bool,
    research_fields: tuple[str, ...],
    text: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list[RankedArticle]:
    filters = RankingFilters(
        min_score=min_score,
        only_highlights=only_highlights,
        only_unvalidated=only_unvalidated,
        research_fields=research_fields,
        text=text or None,
        date_from=date_from,
        date_to=date_to,
    )
    with session_scope() as session:
        return _service(session).get_ranking(version_id, model, filters)


@st.cache_data(ttl=CACHE_SECONDS, show_spinner="Calculando a visão geral...")
def load_overview(version_id: str, model: str) -> Overview:
    with session_scope() as session:
        service = OverviewService(
            ArticleRepository(session),
            AnalysisRepository(session),
            _service(session),
        )
        return service.get_overview(version_id, model)


def reviewers() -> tuple[str, ...]:
    """Nomes autorizados a validar (variável REVISORES); vazio = qualquer nome."""
    return settings.reviewers


def submit_validation(analysis_id: str, reviewer_name: str, agrees: bool, comment: str | None) -> None:
    """Grava a validação (commit ao sair do bloco) e limpa o cache para o ranking refletir."""
    with session_scope() as session:
        service = ValidationService(ValidationRepository(session), allowed_reviewers=reviewers())
        service.submit(analysis_id, reviewer_name, agrees, comment)
    clear_cache()


def clear_cache() -> None:
    st.cache_data.clear()