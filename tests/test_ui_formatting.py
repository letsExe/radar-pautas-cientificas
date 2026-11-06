from datetime import date, datetime, timezone

from app.schemas.ranking_schema import AuthorView, RankedArticle, ValidationView
from app.ui import formatting as f


def make_item(**overrides):
    base = dict(
        analysis_id="a1", openalex_id="W1", title="Água", abstract=None, authors=(),
        source_name=None, publication_date=None, research_field=None, url=None,
        scores={}, justifications={}, general_justification="", approaches=(),
        final_score=7.456, recommended=True, validations=(),
    )
    base.update(overrides)
    return RankedArticle(**base)


def test_data_formatada_e_ausente():
    assert f.format_date(date(2026, 3, 5)) == "05/03/2026"
    assert f.format_date(None) == "data não informada"


def test_autores_da_unila_em_negrito_e_lista_cortada():
    authors = tuple(AuthorView(f"A{i}", unila=(i == 0)) for i in range(8))
    text = f.format_authors(authors, limit=3)
    assert text == "**A0**, A1, A2 e mais 5"
    assert f.format_authors(()) == "autores não informados"


def test_resumo_de_validacoes():
    when = datetime(2026, 11, 1, tzinfo=timezone.utc)
    vs = (ValidationView("Ana", True, None, when), ValidationView("Bia", False, "x", when))
    assert f.validation_summary(vs) == "1 de 2 concordam"
    assert f.validation_summary(()) == "sem validação"


def test_rotulo_do_artigo():
    assert f.article_label(make_item()) == "7.46 · ⭐ Água"
    assert f.article_label(make_item(recommended=False)) == "7.46 · Água"
    longo = f.article_label(make_item(title="x" * 300))
    assert longo.endswith("…") and len(longo) < 130
    assert "\\$" in f.article_label(make_item(title="Custo de $5"))


def test_barra_de_progresso_fica_entre_0_e_1():
    assert f.progress_value(5) == 0.5
    assert f.progress_value(-2) == 0.0 and f.progress_value(14) == 1.0