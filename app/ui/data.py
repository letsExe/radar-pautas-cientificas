"""Acesso a dados para a interface: abre a sessão, chama o serviço e guarda em cache.

Os resultados são objetos simples (schemas), por isso podem ficar em cache com segurança.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from app.core.database import session_scope
from app.repositories.ranking_repository import RankingRepository
from app.schemas.ranking_schema import RankedArticle, RankingFilters, VersionView
from app.services.ranking_service import RankingService

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


def clear_cache() -> None:
    st.cache_data.clear()