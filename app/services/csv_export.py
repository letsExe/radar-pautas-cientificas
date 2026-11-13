"""Exportação em CSV (UTF-8 com BOM, para o Excel abrir os acentos) para a análise do trabalho."""
from __future__ import annotations

import csv
import io
import re
from typing import Iterable

from app.schemas.ranking_schema import RankedArticle, VersionView

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe(value):
    """Texto que começa com =, +, - ou @ viraria fórmula no Excel; o apóstrofo neutraliza."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def _to_bytes(header: list[str], rows: Iterable[list]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([_safe(cell) for cell in row])
    return buffer.getvalue().encode("utf-8-sig")


def analyses_csv(items: Iterable[RankedArticle], version: VersionView) -> bytes:
    """Uma linha por análise, com uma coluna de nota para cada critério da versão."""
    header = (
        ["openalex_id", "titulo", "data_publicacao", "area", "periodico", "url"]
        + [f"nota_{c.id}" for c in version.criteria]
        + ["nota_final", "destaque_ia", "enfoques", "justificativa_geral", "validacoes", "concordam"]
    )
    rows = []
    for item in items:
        rows.append(
            [
                item.openalex_id,
                item.title,
                item.publication_date.isoformat() if item.publication_date else "",
                item.research_field or "",
                item.source_name or "",
                item.url or "",
                *[item.scores.get(c.id, "") for c in version.criteria],
                item.final_score,
                "sim" if item.recommended else "não",
                " | ".join(item.approaches),
                item.general_justification,
                len(item.validations),
                sum(1 for v in item.validations if v.agrees),
            ]
        )
    return _to_bytes(header, rows)


def validations_csv(items: Iterable[RankedArticle]) -> bytes:
    """Uma linha por validação humana, com a nota e o destaque da IA ao lado."""
    header = [
        "openalex_id", "titulo", "nota_final", "destaque_ia",
        "revisor", "concorda", "comentario", "validado_em",
    ]
    rows = []
    for item in items:
        for v in item.validations:
            rows.append(
                [
                    item.openalex_id,
                    item.title,
                    item.final_score,
                    "sim" if item.recommended else "não",
                    v.reviewer_name,
                    "sim" if v.agrees else "não",
                    v.comment or "",
                    v.validated_at.isoformat(),
                ]
            )
    return _to_bytes(header, rows)


def export_filename(kind: str, version_label: str, model: str) -> str:
    """Nome de arquivo seguro, ex.: analises_v1_gemini-3.5-flash-lite.csv"""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{kind}_{version_label}_{model}").strip("-")
    return f"{slug}.csv"