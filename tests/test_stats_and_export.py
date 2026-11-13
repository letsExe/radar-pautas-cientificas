import csv
import io
from datetime import date, datetime, timezone

from app.schemas.ranking_schema import CriterionView, RankedArticle, ValidationView, VersionView
from app.services import csv_export
from app.services.overview_service import OverviewService
from app.services.stats import compute_agreement, score_histogram

WHEN = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def val(reviewer, agrees, comment=None):
    return ValidationView(reviewer, agrees, comment, WHEN)


def item(score=7.0, recommended=True, validations=(), **overrides):
    base = dict(
        analysis_id="a", openalex_id="W1", title="Água", abstract=None, authors=(),
        source_name="Revista", publication_date=date(2026, 3, 1), research_field="Ambiental",
        url="https://x", scores={"a": 8.0, "b": 4.0}, justifications={},
        general_justification="Boa pauta.", approaches=("Impacto local", "Fronteira"),
        final_score=score, recommended=recommended, validations=tuple(validations),
    )
    base.update(overrides)
    return RankedArticle(**base)


VERSION = VersionView(
    id="v", label="v1", config_hash="abc1234", created_at=WHEN, highlight_threshold=6.5,
    criteria=(CriterionView("a", "A", 0.5, ""), CriterionView("b", "B", 0.5, "")),
)


def test_concordancia_geral_por_grupo_e_por_revisor():
    items = [
        item(recommended=True, validations=[val("Ana", True), val("Bia", False)]),
        item(recommended=False, validations=[val("Ana", True)]),
        item(recommended=True),
    ]
    s = compute_agreement(items)
    assert s.articles_validated == 2
    assert (s.overall.total, s.overall.agree) == (3, 2)
    assert (s.on_highlights.total, s.on_highlights.agree) == (2, 1)
    assert (s.on_non_highlights.total, s.on_non_highlights.agree) == (1, 1)
    assert [(n, c.total, c.agree) for n, c in s.by_reviewer] == [("Ana", 2, 2), ("Bia", 1, 0)]
    assert s.overall.rate == 2 / 3


def test_sem_validacoes_a_taxa_e_none():
    s = compute_agreement([item()])
    assert s.overall.total == 0 and s.overall.rate is None and s.by_reviewer == ()


def test_histograma_inclui_10_na_ultima_faixa_e_0_na_primeira():
    h = dict(score_histogram([item(score=0), item(score=0.9), item(score=1), item(score=9.99), item(score=10)]))
    assert h["0–1"] == 2 and h["1–2"] == 1 and h["9–10"] == 2
    assert len(h) == 10 and sum(h.values()) == 5


def parse(content: bytes):
    assert content.startswith(b"\xef\xbb\xbf")  # BOM para o Excel
    return list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))


def test_csv_de_analises_tem_uma_coluna_por_criterio():
    rows = parse(csv_export.analyses_csv([item(validations=[val("Ana", True), val("Bia", False)])], VERSION))
    header, row = rows
    assert "nota_a" in header and "nota_b" in header
    data = dict(zip(header, row))
    assert data["nota_a"] == "8.0" and data["destaque_ia"] == "sim"
    assert data["enfoques"] == "Impacto local | Fronteira"
    assert (data["validacoes"], data["concordam"]) == ("2", "1")


def test_csv_de_validacoes_tem_uma_linha_por_validacao():
    rows = parse(csv_export.validations_csv([item(validations=[val("Ana", True, "ok"), val("Bia", False)]), item()]))
    assert len(rows) == 3
    first = dict(zip(rows[0], rows[1]))
    assert (first["revisor"], first["concorda"], first["comentario"]) == ("Ana", "sim", "ok")


def test_csv_neutraliza_formulas_e_preserva_acentos_e_virgulas():
    risky = item(title="=CMD()", general_justification="Água, fronteira e \"rio\"", validations=[val("Ana", True, "+1")])
    rows = parse(csv_export.analyses_csv([risky], VERSION))
    data = dict(zip(*rows))
    assert data["titulo"] == "'=CMD()" and data["justificativa_geral"] == "Água, fronteira e \"rio\""
    assert dict(zip(*parse(csv_export.validations_csv([risky]))))["comentario"] == "'+1"


def test_nome_do_arquivo_e_seguro():
    assert csv_export.export_filename("analises", "v1", "gemini-3.5-flash-lite") == "analises_v1_gemini-3.5-flash-lite.csv"
    assert csv_export.export_filename("x", "v 1/../a", "m") == "x_v-1-..-a_m.csv"


class FakeArticles:
    def count(self): return 200
    def count_with_abstract(self): return 198


class FakeAnalyses:
    def count_pending(self, version_id, model): return 190


class FakeRanking:
    def get_ranking(self, version_id, model):
        return [item(8.0, True, [val("Ana", True)]), item(3.0, False)]


def test_visao_geral_junta_coleta_concordancia_e_notas():
    overview = OverviewService(FakeArticles(), FakeAnalyses(), FakeRanking()).get_overview("v", "m")
    c = overview.collection
    assert (c.articles, c.with_abstract, c.analyzed, c.pending) == (200, 198, 2, 190)
    assert round(c.abstract_rate, 2) == 0.99
    assert overview.agreement.overall.total == 1 and len(overview.items) == 2
    assert dict(overview.histogram)["8–9"] == 1 and dict(overview.histogram)["3–4"] == 1