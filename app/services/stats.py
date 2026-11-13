"""Cálculos puros sobre o ranking: concordância entre jornalistas e IA, e distribuição de notas."""
from __future__ import annotations

from typing import Iterable

from app.schemas.overview_schema import AgreementCount, AgreementSummary
from app.schemas.ranking_schema import RankedArticle


def _count(votes: list[bool]) -> AgreementCount:
    return AgreementCount(total=len(votes), agree=sum(votes))


def compute_agreement(items: Iterable[RankedArticle]) -> AgreementSummary:
    """Concordância = validações 'concordo' ÷ total de validações (cada revisor conta uma vez por análise)."""
    overall: list[bool] = []
    highlights: list[bool] = []
    others: list[bool] = []
    by_reviewer: dict[str, list[bool]] = {}
    articles_validated = 0

    for item in items:
        if item.validations:
            articles_validated += 1
        for validation in item.validations:
            overall.append(validation.agrees)
            (highlights if item.recommended else others).append(validation.agrees)
            by_reviewer.setdefault(validation.reviewer_name, []).append(validation.agrees)

    return AgreementSummary(
        articles_validated=articles_validated,
        overall=_count(overall),
        on_highlights=_count(highlights),
        on_non_highlights=_count(others),
        by_reviewer=tuple((name, _count(votes)) for name, votes in sorted(by_reviewer.items())),
    )


def score_histogram(
    items: Iterable[RankedArticle], bin_size: int = 1, scale: int = 10
) -> tuple[tuple[str, int], ...]:
    """Quantidade de artigos por faixa de nota (0–1, 1–2, ..., 9–10; o 10 entra na última)."""
    bins = scale // bin_size
    counts = [0] * bins
    for item in items:
        index = min(max(int(item.final_score // bin_size), 0), bins - 1)
        counts[index] += 1
    return tuple((f"{i * bin_size}–{(i + 1) * bin_size}", n) for i, n in enumerate(counts))