"""Consultas de leitura para a interface: devolve objetos simples, nunca objetos do banco."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.ranking_schema import (
    AuthorView,
    CriterionView,
    RankedArticle,
    RankingFilters,
    ValidationView,
    VersionView,
)

if TYPE_CHECKING:
    from app.repositories.ranking_repository import RankingRepository


def _version_view(version) -> VersionView:
    raw = version.config or {}
    criteria = tuple(
        CriterionView(
            id=str(c["id"]),
            name=str(c["nome"]),
            weight=float(c["peso"]),
            description=" ".join(str(c.get("descricao", "")).split()),
        )
        for c in raw.get("criterios", [])
    )
    return VersionView(
        id=str(version.id),
        label=version.version_label or "sem rótulo",
        config_hash=version.config_hash,
        created_at=version.created_at,
        highlight_threshold=float(raw.get("limiar_destaque", 6.5)),
        criteria=criteria,
    )


def _ranked_article(analysis) -> RankedArticle:
    article = analysis.article
    return RankedArticle(
        analysis_id=str(analysis.id),
        openalex_id=article.openalex_id,
        title=article.title,
        abstract=article.abstract,
        authors=tuple(
            AuthorView(name=a.get("name") or "?", unila=bool(a.get("unila")))
            for a in (article.authors or [])
        ),
        source_name=article.source_name,
        publication_date=article.publication_date,
        research_field=article.research_field,
        url=article.url,
        scores={k: float(v) for k, v in (analysis.scores or {}).items()},
        justifications=dict(analysis.justificativas or {}),
        general_justification=analysis.justificativa_geral or "",
        approaches=tuple(analysis.enfoques or ()),
        final_score=float(analysis.score_final),
        recommended=bool(analysis.recomendado),
        validations=tuple(
            ValidationView(v.reviewer_name, v.agrees, v.comment, v.validated_at)
            for v in sorted(analysis.validations, key=lambda v: v.validated_at)
        ),
    )


class RankingService:
    def __init__(self, repository: RankingRepository) -> None:
        self._repository = repository

    def list_versions(self) -> list[VersionView]:
        return [_version_view(v) for v in self._repository.list_versions()]

    def list_models(self, version_id: str) -> list[str]:
        return self._repository.list_models(version_id)

    def list_research_fields(self, version_id: str, model: str) -> list[str]:
        return self._repository.list_research_fields(version_id, model)

    def get_ranking(
        self, version_id: str, model: str, filters: RankingFilters | None = None
    ) -> list[RankedArticle]:
        analyses = self._repository.list_analyses(version_id, model, filters or RankingFilters())
        return [_ranked_article(a) for a in analyses]