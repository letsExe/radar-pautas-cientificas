"""Visão geral: números da coleta, concordância entre jornalistas e IA, notas e exportação."""
from __future__ import annotations

import streamlit as st

from app.schemas.overview_schema import AgreementSummary, CollectionStats, Overview
from app.schemas.ranking_schema import VersionView
from app.services import csv_export
from app.ui import data
from app.ui.formatting import format_percent, version_label


def _render_collection(stats: CollectionStats) -> None:
    st.subheader("Coleta e análise")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Artigos coletados", stats.articles)
    c2.metric("Com resumo", stats.with_abstract, format_percent(stats.abstract_rate), delta_color="off")
    c3.metric("Analisados pela IA", stats.analyzed)
    c4.metric("Pendentes", stats.pending)
    st.caption("Artigos sem resumo no OpenAlex são salvos, mas não são enviados à IA.")


def _render_agreement(summary: AgreementSummary) -> None:
    st.subheader("Concordância entre jornalistas e IA")
    if summary.overall.total == 0:
        st.info("Ainda não há validações. Elas aparecem aqui assim que os jornalistas validarem artigos.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Artigos validados", summary.articles_validated)
    c2.metric("Concordância geral", format_percent(summary.overall.rate), f"{summary.overall.total} validações", delta_color="off")
    c3.metric("Nos destaques da IA", format_percent(summary.on_highlights.rate), f"{summary.on_highlights.total} validações", delta_color="off")
    c4.metric("Fora dos destaques", format_percent(summary.on_non_highlights.rate), f"{summary.on_non_highlights.total} validações", delta_color="off")
    st.caption(
        "Concordância = validações “Concordo” ÷ total de validações. "
        "Com poucas validações o percentual oscila muito: leia junto com o número ao lado."
    )
    st.dataframe(
        [
            {"Revisor": name, "Validações": c.total, "Concordam": c.agree, "Concordância": format_percent(c.rate)}
            for name, c in summary.by_reviewer
        ],
        hide_index=True,
        use_container_width=True,
    )


def _render_histogram(overview: Overview) -> None:
    st.subheader("Distribuição das notas finais")
    st.bar_chart(
        [{"Faixa de nota": label, "Artigos": count} for label, count in overview.histogram],
        x="Faixa de nota",
        y="Artigos",
    )


def _render_export(overview: Overview, version: VersionView, model: str) -> None:
    st.subheader("Exportar dados")
    st.caption("CSV em UTF-8 (abre com acentos no Excel e no Google Planilhas), para a análise do trabalho.")
    c1, c2 = st.columns(2)
    c1.download_button(
        "Baixar análises (uma linha por artigo)",
        data=csv_export.analyses_csv(overview.items, version),
        file_name=csv_export.export_filename("analises", version.label, model),
        mime="text/csv",
    )
    c2.download_button(
        "Baixar validações (uma linha por validação)",
        data=csv_export.validations_csv(overview.items),
        file_name=csv_export.export_filename("validacoes", version.label, model),
        mime="text/csv",
        disabled=overview.agreement.overall.total == 0,
    )


def render() -> None:
    st.subheader("Qual análise você quer ver?")
    versions = [v for v in data.load_versions() if data.load_models(v.id)]
    if not versions:
        st.info("Ainda não há análises. Rode o pipeline: `poetry run python -m app.cli`.")
        return

    col_version, col_model = st.columns(2)
    version = col_version.selectbox(
        "Versão dos critérios", versions, format_func=version_label, key="overview-version"
    )
    model = col_model.selectbox("Modelo de IA", data.load_models(version.id), key="overview-model")

    overview = data.load_overview(version.id, model)
    _render_collection(overview.collection)
    _render_agreement(overview.agreement)
    _render_histogram(overview)
    _render_export(overview, version, model)