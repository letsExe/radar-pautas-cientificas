from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Article

# Campos que podem ser atualizados em coletas futuras (o OpenAlex às vezes completa dados,
# como o resumo). O id e a data da primeira coleta nunca mudam.
UPDATABLE = (
    "title", "abstract", "authors", "publication_date", "source_name", "doi",
    "url", "work_type", "language", "topic", "research_field",
)
COLUMNS = ("openalex_id", *UPDATABLE)


def _to_row(article: dict) -> dict:
    row = {col: article.get(col) for col in COLUMNS}
    if isinstance(row["publication_date"], str):
        row["publication_date"] = date.fromisoformat(row["publication_date"])
    return row


class ArticleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, articles: list[dict], batch_size: int = 100) -> int:
        """Insere os artigos novos e atualiza os existentes (chave: openalex_id).

        Devolve quantos artigos distintos foram processados. Não faz commit.
        """
        # Duplicatas no mesmo lote fariam o ON CONFLICT falhar; ficamos com uma por id.
        unique = {a["openalex_id"]: a for a in articles if a.get("openalex_id")}
        rows = [_to_row(a) for a in unique.values()]

        for start in range(0, len(rows), batch_size):
            stmt = insert(Article).values(rows[start : start + batch_size])
            stmt = stmt.on_conflict_do_update(
                index_elements=[Article.openalex_id],
                set_={col: stmt.excluded[col] for col in UPDATABLE},
            )
            self._session.execute(stmt)
        return len(rows)

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Article)) or 0

    def count_with_abstract(self) -> int:
        stmt = select(func.count()).select_from(Article).where(Article.abstract.is_not(None))
        return self._session.scalar(stmt) or 0