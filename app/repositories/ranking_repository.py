from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, contains_eager, selectinload

from app.models import Analysis, Article, PromptVersion
from app.schemas.ranking_schema import RankingFilters


class RankingRepository:
    """Consultas de leitura usadas pela interface (ranking, filtros e opções)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_versions(self) -> list[PromptVersion]:
        stmt = select(PromptVersion).order_by(PromptVersion.created_at.desc())
        return list(self._session.scalars(stmt))

    def list_models(self, prompt_version_id: UUID) -> list[str]:
        stmt = (
            select(Analysis.llm_model)
            .where(Analysis.prompt_version_id == prompt_version_id)
            .distinct()
            .order_by(Analysis.llm_model)
        )
        return list(self._session.scalars(stmt))

    def list_research_fields(self, prompt_version_id: UUID, model: str) -> list[str]:
        stmt = (
            select(Article.research_field)
            .join(Analysis, Analysis.article_id == Article.id)
            .where(
                Analysis.prompt_version_id == prompt_version_id,
                Analysis.llm_model == model,
                Article.research_field.is_not(None),
            )
            .distinct()
            .order_by(Article.research_field)
        )
        return list(self._session.scalars(stmt))

    def list_analyses(
        self, prompt_version_id: UUID, model: str, filters: RankingFilters
    ) -> list[Analysis]:
        """Análises com artigo e validações já carregados, da maior para a menor nota."""
        stmt = (
            select(Analysis)
            .join(Analysis.article)
            .options(contains_eager(Analysis.article), selectinload(Analysis.validations))
            .where(
                Analysis.prompt_version_id == prompt_version_id,
                Analysis.llm_model == model,
                Analysis.score_final >= filters.min_score,
            )
            .order_by(
                Analysis.score_final.desc(),
                Article.publication_date.desc().nulls_last(),
                Analysis.id,
            )
        )
        if filters.only_highlights:
            stmt = stmt.where(Analysis.recomendado.is_(True))
        if filters.only_unvalidated:
            stmt = stmt.where(~Analysis.validations.any())
        if filters.research_fields:
            stmt = stmt.where(Article.research_field.in_(filters.research_fields))
        if filters.text:
            stmt = stmt.where(
                or_(
                    Article.title.icontains(filters.text, autoescape=True),
                    Article.abstract.icontains(filters.text, autoescape=True),
                )
            )
        if filters.date_from:
            stmt = stmt.where(Article.publication_date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Article.publication_date <= filters.date_to)
        if filters.limit:
            stmt = stmt.limit(filters.limit)
        return list(self._session.scalars(stmt))