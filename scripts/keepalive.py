"""Consulta mínima ao banco para o Supabase (plano gratuito) não pausar por inatividade.

Uso: python -m scripts.keepalive
Em log público, imprime só o tipo do erro, nunca a mensagem (que pode citar o endereço do banco).
"""
from __future__ import annotations

import sys
from typing import Callable, ContextManager


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
    from app.core.database import session_scope

    return run(session_scope)


if __name__ == "__main__":
    sys.exit(main())