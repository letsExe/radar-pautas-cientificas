"""Formatos de dados que a interface recebe: objetos simples, sem ligação com o banco."""
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class CriterionView:
    id: str
    name: str
    weight: float
    description: str


@dataclass(frozen=True)
class VersionView:
    """Uma versão dos critérios (registrada em prompt_versions)."""

    id: str
    label: str
    config_hash: str
    created_at: datetime
    highlight_threshold: float
    criteria: tuple[CriterionView, ...]


@dataclass(frozen=True)
class AuthorView:
    name: str
    unila: bool


@dataclass(frozen=True)
class ValidationView:
    reviewer_name: str
    agrees: bool
    comment: str | None
    validated_at: datetime


@dataclass(frozen=True)
class RankedArticle:
    """Um artigo com a análise da IA e as validações humanas, pronto para exibir."""

    analysis_id: str
    openalex_id: str
    title: str
    abstract: str | None
    authors: tuple[AuthorView, ...]
    source_name: str | None
    publication_date: date | None
    research_field: str | None
    url: str | None
    scores: dict[str, float]
    justifications: dict[str, str]
    general_justification: str
    approaches: tuple[str, ...]
    final_score: float
    recommended: bool
    validations: tuple[ValidationView, ...]


@dataclass(frozen=True)
class RankingFilters:
    min_score: float = 0.0
    only_highlights: bool = False
    only_unvalidated: bool = False
    research_fields: tuple[str, ...] = ()
    text: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: int | None = None