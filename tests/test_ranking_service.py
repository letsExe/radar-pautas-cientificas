from datetime import date, datetime, timezone
from types import SimpleNamespace as NS

from app.schemas.ranking_schema import RankingFilters
from app.services.ranking_service import RankingService


def make_analysis(**overrides):
    article = NS(
        openalex_id="W1",
        title="Água na fronteira",
        abstract="Resumo.",
        authors=[{"name": "Ana", "unila": True}, {"name": "Bob", "unila": False}, {"name": None}],
        source_name="Revista X",
        publication_date=date(2026, 10, 1),
        research_field="Ciências Ambientais",
        url="https://doi.org/x",
    )
    base = dict(
        id="an-1",
        article=article,
        scores={"a": 8, "b": 4},
        justificativas={"a": "ok"},
        justificativa_geral="Boa pauta.",
        enfoques=["Impacto local"],
        score_final=7.0,
        recomendado=True,
        validations=[
            NS(reviewer_name="Maria", agrees=False, comment="discordo",
               validated_at=datetime(2026, 11, 2, tzinfo=timezone.utc)),
            NS(reviewer_name="João", agrees=True, comment=None,
               validated_at=datetime(2026, 11, 1, tzinfo=timezone.utc)),
        ],
    )
    base.update(overrides)
    return NS(**base)


class FakeRepository:
    def __init__(self, analyses=(), versions=()):
        self.analyses = list(analyses)
        self.versions = list(versions)
        self.received = None

    def list_versions(self):
        return self.versions

    def list_models(self, version_id):
        return ["fake-model"]

    def list_research_fields(self, version_id, model):
        return ["Ciências Ambientais"]

    def list_analyses(self, version_id, model, filters):
        self.received = (version_id, model, filters)
        return self.analyses


def test_converte_a_analise_em_objeto_simples():
    [item] = RankingService(FakeRepository([make_analysis()])).get_ranking("v1", "fake-model")
    assert item.title == "Água na fronteira" and item.final_score == 7.0 and item.recommended
    assert [(a.name, a.unila) for a in item.authors] == [("Ana", True), ("Bob", False), ("?", False)]
    assert item.scores == {"a": 8.0, "b": 4.0} and item.approaches == ("Impacto local",)
    # validações em ordem cronológica
    assert [v.reviewer_name for v in item.validations] == ["João", "Maria"]


def test_campos_opcionais_ausentes_nao_quebram():
    analysis = make_analysis(enfoques=None, justificativa_geral=None, justificativas=None, validations=[])
    analysis.article.authors = None
    [item] = RankingService(FakeRepository([analysis])).get_ranking("v1", "fake-model")
    assert item.approaches == () and item.general_justification == "" and item.authors == ()
    assert item.validations == ()


def test_filtros_chegam_ao_repositorio():
    repository = FakeRepository()
    filters = RankingFilters(min_score=6.5, only_highlights=True, limit=10)
    RankingService(repository).get_ranking("v1", "fake-model", filters)
    assert repository.received == ("v1", "fake-model", filters)


def test_sem_filtros_usa_os_padroes():
    repository = FakeRepository()
    RankingService(repository).get_ranking("v1", "fake-model")
    assert repository.received[2] == RankingFilters()


def test_converte_a_versao_dos_criterios():
    version = NS(
        id="v-1",
        version_label="v1",
        config_hash="abc123",
        created_at=datetime(2026, 11, 3, tzinfo=timezone.utc),
        config={
            "limiar_destaque": 6.5,
            "criterios": [
                {"id": "a", "nome": "Critério A", "peso": 0.75, "descricao": "Linha 1\n  linha 2"},
                {"id": "b", "nome": "Critério B", "peso": 0.25},
            ],
        },
    )
    [view] = RankingService(FakeRepository(versions=[version])).list_versions()
    assert view.label == "v1" and view.highlight_threshold == 6.5
    assert [(c.id, c.name, c.weight) for c in view.criteria] == [("a", "Critério A", 0.75), ("b", "Critério B", 0.25)]
    assert view.criteria[0].description == "Linha 1 linha 2"