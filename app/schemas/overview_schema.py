"""Formatos dos números da visão geral (coleta, concordância e distribuição de notas)."""
from dataclasses import dataclass

from app.schemas.ranking_schema import RankedArticle


@dataclass(frozen=True)
class CollectionStats:
    articles: int
    with_abstract: int
    analyzed: int
    pending: int

    @property
    def abstract_rate(self) -> float | None:
        return self.with_abstract / self.articles if self.articles else None


@dataclass(frozen=True)
class AgreementCount:
    total: int
    agree: int

    @property
    def rate(self) -> float | None:
        return self.agree / self.total if self.total else None


@dataclass(frozen=True)
class AgreementSummary:
    articles_validated: int
    overall: AgreementCount
    on_highlights: AgreementCount
    on_non_highlights: AgreementCount
    by_reviewer: tuple[tuple[str, AgreementCount], ...]


@dataclass(frozen=True)
class Overview:
    collection: CollectionStats
    agreement: AgreementSummary
    histogram: tuple[tuple[str, int], ...]
    items: tuple[RankedArticle, ...]