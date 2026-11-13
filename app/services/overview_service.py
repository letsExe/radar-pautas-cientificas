"""Monta a visão geral: números da coleta, concordância humana x IA e distribuição de notas."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.overview_schema import CollectionStats, Overview
from app.services.stats import compute_agreement, score_histogram

if TYPE_CHECKING:
    from app.repositories.analysis_repository import AnalysisRepository
    from app.repositories.article_repository import ArticleRepository
    from app.services.ranking_service import RankingService


class OverviewService:
    def __init__(
        self,
        articles: ArticleRepository,
        analyses: AnalysisRepository,
        ranking: RankingService,
    ) -> None:
        self._articles = articles
        self._analyses = analyses
        self._ranking = ranking

    def get_overview(self, version_id: str, model: str) -> Overview:
        items = tuple(self._ranking.get_ranking(version_id, model))
        collection = CollectionStats(
            articles=self._articles.count(),
            with_abstract=self._articles.count_with_abstract(),
            analyzed=len(items),
            pending=self._analyses.count_pending(version_id, model),
        )
        return Overview(
            collection=collection,
            agreement=compute_agreement(items),
            histogram=score_histogram(items),
            items=items,
        )