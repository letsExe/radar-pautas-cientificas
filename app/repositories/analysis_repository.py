from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Analysis, Article
from app.schemas.analysis_schema import AnalysisResult

REPLACEABLE = (
    "scores", "justificativas", "justificativa_geral", "enfoques", "score_final", "recomendado",
)


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, article_id: UUID, prompt_version_id: UUID, result: AnalysisResult) -> None:
        """Grava a análise; se já existir para (artigo, versão, modelo), substitui. Não faz commit."""
        stmt = insert(Analysis).values(
            article_id=article_id,
            prompt_version_id=prompt_version_id,
            llm_model=result.model,
            scores=result.scores,
            justificativas=result.justifications,
            justificativa_geral=result.general_justification,
            enfoques=list(result.approaches),
            score_final=result.final_score,
            recomendado=result.recommended,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Analysis.article_id, Analysis.prompt_version_id, Analysis.llm_model],
            set_={**{col: stmt.excluded[col] for col in REPLACEABLE}, "analyzed_at": func.now()},
        )
        self._session.execute(stmt)

    def _pending_conditions(self, prompt_version_id: UUID, model: str) -> tuple:
        """Artigos com resumo e sem análise desta versão de critérios e deste modelo."""
        already_analyzed = (
            select(Analysis.id)
            .where(
                Analysis.article_id == Article.id,
                Analysis.prompt_version_id == prompt_version_id,
                Analysis.llm_model == model,
            )
            .exists()
        )
        return (Article.abstract.is_not(None), Article.abstract != "", ~already_analyzed)

    def list_pending(
        self, prompt_version_id: UUID, model: str, limit: int | None = None
    ) -> list[Article]:
        stmt = (
            select(Article)
            .where(*self._pending_conditions(prompt_version_id, model))
            .order_by(Article.publication_date.desc().nulls_last(), Article.id)
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self._session.scalars(stmt))

    def count_pending(self, prompt_version_id: UUID, model: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Article)
            .where(*self._pending_conditions(prompt_version_id, model))
        )
        return self._session.scalar(stmt) or 0