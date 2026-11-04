import time
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.llm import LLMError
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_validator import AnalysisError
from app.services.article_analyzer import ArticleAnalyzer

# (posição atual, total, título do artigo), útil para barras de progresso
ProgressCallback = Callable[[int, int, str], None]


@dataclass(frozen=True)
class AnalysisFailure:
    openalex_id: str
    reason: str


@dataclass(frozen=True)
class AnalysisRunResult:
    analyzed: int
    failures: tuple[AnalysisFailure, ...]
    remaining: int  # artigos que continuam pendentes para uma próxima execução
    stopped_early: bool  # True se parou por falhas seguidas (ex.: cota esgotada)


class AnalysisService:
    """Analisa os artigos pendentes, um a um, gravando cada resultado assim que fica pronto."""

    def __init__(
        self,
        session: Session,
        repository: AnalysisRepository,
        analyzer: ArticleAnalyzer,
        prompt_version_id: UUID,
        delay_seconds: float = 0.0,
        max_consecutive_failures: int = 5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._session = session
        self._repository = repository
        self._analyzer = analyzer
        self._prompt_version_id = prompt_version_id
        self._delay_seconds = delay_seconds
        self._max_consecutive_failures = max_consecutive_failures
        self._sleep = sleep

    def run(
        self, limit: int | None = None, on_progress: ProgressCallback | None = None
    ) -> AnalysisRunResult:
        model = self._analyzer.model_name
        pending = self._repository.list_pending(self._prompt_version_id, model, limit)

        analyzed = 0
        consecutive_failures = 0
        stopped_early = False
        failures: list[AnalysisFailure] = []

        for position, article in enumerate(pending, start=1):
            if on_progress:
                on_progress(position, len(pending), article.title)
            try:
                result = self._analyzer.analyze(article)
                self._repository.save(article.id, self._prompt_version_id, result)
                self._session.commit()  # commit por artigo: o que já foi pago à LLM não se perde
            except (LLMError, AnalysisError, SQLAlchemyError) as exc:
                self._session.rollback()
                failures.append(AnalysisFailure(article.openalex_id, str(exc)[:300]))
                consecutive_failures += 1
                if consecutive_failures >= self._max_consecutive_failures:
                    stopped_early = True
                    break
            else:
                analyzed += 1
                consecutive_failures = 0

            if position < len(pending):
                self._sleep(self._delay_seconds)

        remaining = self._repository.count_pending(self._prompt_version_id, model)
        return AnalysisRunResult(analyzed, tuple(failures), remaining, stopped_early)