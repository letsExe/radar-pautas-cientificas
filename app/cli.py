"""Linha de comando do Radar.

Exemplos:
    poetry run python -m app.cli --limit 20
    poetry run python -m app.cli --since 2026-06-01 --max-collect 200 --limit 50
    poetry run python -m app.cli --skip-collect --limit 30
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.pipeline_service import PipelineResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Coleta artigos da UNILA no OpenAlex e analisa o potencial de pauta com IA.",
    )
    parser.add_argument(
        "--since",
        type=date.fromisoformat,
        default=date(date.today().year, 1, 1),
        metavar="AAAA-MM-DD",
        help="coleta artigos publicados a partir desta data (padrão: 1º de janeiro deste ano)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="máximo de artigos a analisar nesta execução; 0 = sem limite (padrão: 20)",
    )
    parser.add_argument(
        "--max-collect",
        type=int,
        default=None,
        help="máximo de artigos a coletar (útil em testes)",
    )
    parser.add_argument(
        "--skip-collect",
        action="store_true",
        help="não consulta o OpenAlex; só analisa os artigos pendentes que já estão no banco",
    )
    parser.add_argument(
        "--provider",
        default=None,
        help="provedor de LLM (padrão: LLM_PROVIDER do .env)",
    )
    return parser


def _show_progress(position: int, total: int, title: str) -> None:
    print(f"[{position}/{total}] {title[:70]}", flush=True)


def print_summary(result: PipelineResult) -> None:
    if result.collection:
        c = result.collection
        print(f"Coleta: {c.collected} artigos ({c.without_abstract} sem resumo)")
    a = result.analysis
    print(f"Análise: {a.analyzed} analisados, {len(a.failures)} falhas, {a.remaining} pendentes")
    for failure in a.failures:
        print(f"  - {failure.openalex_id}: {failure.reason}")
    if a.stopped_early:
        print("Interrompido por falhas seguidas: verifique a chave da API, a cota e a rede.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Importações aqui dentro: --help e erros de argumento não dependem de banco nem de chaves.
    from app.bootstrap import build_pipeline
    from app.core.database import session_scope

    try:
        with session_scope() as session:
            pipeline = build_pipeline(session, args.provider)
            result = pipeline.run(
                since=args.since.isoformat(),
                collect=not args.skip_collect,
                max_collect=args.max_collect,
                analysis_limit=args.limit or None,
                on_progress=_show_progress,
            )
    except (RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print_summary(result)
    return 1 if result.analysis.stopped_early else 0


if __name__ == "__main__":
    sys.exit(main())