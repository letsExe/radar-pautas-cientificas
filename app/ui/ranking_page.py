"""Tela de ranking: filtros na barra lateral e lista de artigos ordenada por nota."""
from __future__ import annotations

import streamlit as st

from app.schemas.ranking_schema import RankedArticle, VersionView
from app.ui import data
from app.ui.formatting import (
    article_label,
    escape_markdown,
    format_authors,
    format_date,
    progress_value,
    validation_summary,
)


def _version_label(version: VersionView) -> str:
    return f"{version.label} · {version.created_at:%d/%m/%Y} · {version.config_hash[:7]}"


def _render_sidebar() -> dict | None:
    """Desenha os filtros e devolve as escolhas; None se ainda não há análises."""
    st.sidebar.header("Filtros")

    versions = [v for v in data.load_versions() if data.load_models(v.id)]
    if not versions:
        return None
    version = st.sidebar.selectbox("Versão dos critérios", versions, format_func=_version_label)
    model = st.sidebar.selectbox("Modelo de IA", data.load_models(version.id))

    min_score = st.sidebar.slider("Nota mínima", 0.0, 10.0, 0.0, 0.5)
    only_highlights = st.sidebar.checkbox(
        f"Só destaques (nota ≥ {version.highlight_threshold})"
    )
    only_unvalidated = st.sidebar.checkbox("Só sem validação humana")
    fields = st.sidebar.multiselect("Área de pesquisa", data.load_research_fields(version.id, model))
    text = st.sidebar.text_input("Buscar no título ou resumo").strip()
    date_from = st.sidebar.date_input("Publicado a partir de", value=None, format="DD/MM/YYYY")
    date_to = st.sidebar.date_input("Publicado até", value=None, format="DD/MM/YYYY")
    shown = st.sidebar.number_input("Quantidade exibida", min_value=5, max_value=500, value=20, step=5)

    with st.sidebar.expander("Critérios desta versão"):
        for c in version.criteria:
            st.markdown(f"**{c.name}** · peso {c.weight:.0%}")
            st.caption(c.description)

    if st.sidebar.button("Atualizar dados"):
        data.clear_cache()
        st.rerun()

    return {
        "version": version,
        "model": model,
        "shown": int(shown),
        "filters": dict(
            min_score=min_score,
            only_highlights=only_highlights,
            only_unvalidated=only_unvalidated,
            research_fields=tuple(fields),
            text=text or None,
            date_from=date_from,
            date_to=date_to,
        ),
    }


def _render_analysis_tab(item: RankedArticle, version: VersionView) -> None:
    st.markdown(f"**Por que pode virar pauta:** {escape_markdown(item.general_justification)}")
    if item.approaches:
        st.markdown("**Enfoques sugeridos**")
        for approach in item.approaches:
            st.markdown(f"- {escape_markdown(approach)}")
    st.markdown("**Notas por critério**")
    for criterion in version.criteria:
        score = item.scores.get(criterion.id)
        if score is None:
            continue
        st.progress(
            progress_value(score),
            text=f"{criterion.name} · {score:.1f}/10 (peso {criterion.weight:.0%})",
        )
        justification = item.justifications.get(criterion.id)
        if justification:
            st.caption(escape_markdown(justification))


def _render_validations_tab(item: RankedArticle) -> None:
    if not item.validations:
        st.caption("Nenhum jornalista validou esta análise ainda.")
        return
    for v in item.validations:
        verdict = "concorda" if v.agrees else "discorda"
        st.markdown(f"**{v.reviewer_name}** {verdict} · {v.validated_at:%d/%m/%Y %H:%M}")
        if v.comment:
            st.caption(escape_markdown(v.comment))


def _render_article(item: RankedArticle, version: VersionView) -> None:
    with st.expander(article_label(item)):
        meta = [format_authors(item.authors)]
        if item.source_name:
            meta.append(f"*{escape_markdown(item.source_name)}*")
        meta.append(format_date(item.publication_date))
        if item.research_field:
            meta.append(item.research_field)
        st.markdown(" · ".join(meta))
        st.caption(f"Validação: {validation_summary(item.validations)}")
        if item.url:
            st.link_button("Abrir artigo", item.url)

        tab_analysis, tab_abstract, tab_validation = st.tabs(
            ["Análise da IA", "Resumo do artigo", "Validações"]
        )
        with tab_analysis:
            _render_analysis_tab(item, version)
        with tab_abstract:
            st.write(item.abstract or "Resumo não disponível.")
        with tab_validation:
            _render_validations_tab(item)


def render() -> None:
    choices = _render_sidebar()
    if choices is None:
        st.info("Ainda não há análises. Rode o pipeline: `poetry run python -m app.cli`.")
        return

    version: VersionView = choices["version"]
    items = data.load_ranking(version.id, choices["model"], **choices["filters"])

    col_total, col_highlights, col_validated = st.columns(3)
    col_total.metric("Artigos no filtro", len(items))
    col_highlights.metric("Destaques", sum(1 for i in items if i.recommended))
    col_validated.metric("Com validação humana", sum(1 for i in items if i.validations))

    if not items:
        st.warning("Nenhum artigo atende aos filtros escolhidos.")
        return

    shown = choices["shown"]
    st.caption(f"Mostrando {min(shown, len(items))} de {len(items)}, da maior para a menor nota.")
    for item in items[:shown]:
        _render_article(item, version)