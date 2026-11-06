"""Funções puras de apresentação (sem Streamlit), fáceis de testar."""
from __future__ import annotations

from datetime import date
from typing import Sequence

from app.schemas.ranking_schema import AuthorView, RankedArticle, ValidationView


def escape_markdown(text: str) -> str:
    """Evita que '$' vire fórmula em rótulos e textos do Streamlit."""
    return text.replace("$", "\\$")


def format_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else "data não informada"


def format_authors(authors: Sequence[AuthorView], limit: int = 6) -> str:
    """Autores da UNILA em negrito; corta a lista longa."""
    if not authors:
        return "autores não informados"
    names = [f"**{a.name}**" if a.unila else a.name for a in authors[:limit]]
    text = ", ".join(names)
    hidden = len(authors) - limit
    if hidden > 0:
        text += f" e mais {hidden}"
    return text


def validation_summary(validations: Sequence[ValidationView]) -> str:
    if not validations:
        return "sem validação"
    agree = sum(1 for v in validations if v.agrees)
    return f"{agree} de {len(validations)} concordam"


def article_label(item: RankedArticle, max_title: int = 110) -> str:
    title = item.title if len(item.title) <= max_title else item.title[: max_title - 1].rstrip() + "…"
    star = "⭐ " if item.recommended else ""
    return escape_markdown(f"{item.final_score:.2f} · {star}{title}")


def progress_value(score: float, scale: float = 10.0) -> float:
    """Converte a nota (0 a 10) em fração de 0 a 1 para a barra de progresso."""
    return min(max(score / scale, 0.0), 1.0)