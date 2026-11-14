"""Consulta mínima ao banco para o Supabase (plano gratuito) não pausar por inatividade.

Uso: python -m scripts.keepalive
Em log público, imprime só o tipo do erro e dicas sobre o FORMATO da URL, nunca o conteúdo dela.
"""
from __future__ import annotations

import os
import sys
from typing import Callable, ContextManager


def url_format_hints(url: str) -> list[str]:
    """Problemas comuns de formato na DATABASE_URL, descritos sem revelar o valor."""
    hints: list[str] = []
    if not url:
        return ["a variável DATABASE_URL está vazia ou não foi definida"]
    if url != url.strip():
        hints.append("o valor tem espaço ou quebra de linha no começo ou no fim")
    value = url.strip()
    if value[:1] in ("'", '"') or value[-1:] in ("'", '"'):
        hints.append("o valor tem aspas no começo ou no fim; cadastre sem aspas")
    if value.strip("'\"").startswith("DATABASE_URL="):
        hints.append("o valor começa com 'DATABASE_URL='; cadastre só o que vem depois do '='")
    if not value.strip("'\"").startswith(("postgresql://", "postgres://", "postgresql+")):
        hints.append("o valor não começa com postgresql://")
    arrobas = value.count("@")
    if arrobas != 1:
        hints.append(f"o valor tem {arrobas} sinais '@' (o certo é 1); codifique o '@' da senha como %40")
    return hints


def run(open_session: Callable[[], ContextManager]) -> int:
    from sqlalchemy import text

    try:
        with open_session() as session:
            articles = session.scalar(text("select count(*) from articles"))
            analyses = session.scalar(text("select count(*) from analyses"))
    except Exception as error:  # noqa: BLE001 - qualquer falha deve virar código de saída 1
        print(f"Falha ao consultar o banco: {type(error).__name__}", file=sys.stderr)
        return 1
    print(f"Banco ativo: {articles} artigos, {analyses} análises.")
    return 0


def main() -> int:
    try:
        from app.core.database import session_scope
    except Exception as error:  # noqa: BLE001 - o motor do banco é criado ao importar
        print(f"Falha ao configurar o banco: {type(error).__name__}", file=sys.stderr)
        for hint in url_format_hints(os.environ.get("DATABASE_URL", "")):
            print(f"Dica: {hint}", file=sys.stderr)
        return 1
    return run(session_scope)


if __name__ == "__main__":
    sys.exit(main())