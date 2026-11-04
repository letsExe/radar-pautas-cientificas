from collections.abc import Callable, Iterable
from dataclasses import dataclass

from app.core.openalex_client import fetch_works
from app.repositories.article_repository import ArticleRepository

Fetcher = Callable[..., Iterable[dict]]


@dataclass(frozen=True)
class CollectionResult:
    collected: int
    without_abstract: int


class CollectionService:
    """Busca artigos na fonte e grava todos no banco (inclusive os sem resumo)."""

    def __init__(self, repository: ArticleRepository, fetcher: Fetcher = fetch_works) -> None:
        self._repository = repository
        self._fetcher = fetcher

    def collect(
        self, institution_id: str, since: str, max_results: int | None = None
    ) -> CollectionResult:
        articles = list(self._fetcher(institution_id, since=since, max_results=max_results))
        saved = self._repository.upsert_many(articles)
        without_abstract = sum(1 for a in articles if not a.get("abstract"))
        return CollectionResult(collected=saved, without_abstract=without_abstract)