from app.core.llm import LLMError
from app.schemas.analysis_schema import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.services.analysis_validator import AnalysisError

RESULT = AnalysisResult(
    scores={"a": 8.0},
    justifications={"a": "ok"},
    general_justification="Boa pauta.",
    approaches=("Impacto local",),
    final_score=8.0,
    recommended=True,
    model="fake-model",
)


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FakeArticle:
    def __init__(self, n):
        self.id = f"id-{n}"
        self.openalex_id = f"W{n}"
        self.title = f"Artigo {n}"


class FakeRepository:
    def __init__(self, total):
        self.pending = [FakeArticle(n) for n in range(1, total + 1)]
        self.saved = []

    def list_pending(self, prompt_version_id, model, limit=None):
        return self.pending[:limit] if limit else list(self.pending)

    def save(self, article_id, prompt_version_id, result):
        self.saved.append(article_id)

    def count_pending(self, prompt_version_id, model):
        return len(self.pending) - len(self.saved)


class FakeAnalyzer:
    model_name = "fake-model"

    def __init__(self, failing=(), error=AnalysisError):
        self.failing = set(failing)
        self.error = error

    def analyze(self, article):
        if article.openalex_id in self.failing:
            raise self.error("falhou")
        return RESULT


def make_service(total, analyzer=None, **kwargs):
    session, repository = FakeSession(), FakeRepository(total)
    service = AnalysisService(
        session, repository, analyzer or FakeAnalyzer(), "version-1", **kwargs
    )
    return service, session, repository


def test_analisa_todos_e_faz_commit_por_artigo():
    service, session, repository = make_service(3)
    result = service.run()
    assert result.analyzed == 3 and result.failures == () and result.remaining == 0
    assert session.commits == 3 and repository.saved == ["id-1", "id-2", "id-3"]


def test_falha_em_um_artigo_nao_interrompe_os_demais():
    service, session, repository = make_service(3, FakeAnalyzer(failing={"W2"}))
    result = service.run()
    assert result.analyzed == 2 and result.stopped_early is False
    assert [f.openalex_id for f in result.failures] == ["W2"]
    assert session.rollbacks == 1 and repository.saved == ["id-1", "id-3"]
    assert result.remaining == 1  # o que falhou continua pendente


def test_para_depois_de_falhas_seguidas():
    everything = {f"W{n}" for n in range(1, 7)}
    service, _, _ = make_service(
        6, FakeAnalyzer(failing=everything, error=LLMError), max_consecutive_failures=3
    )
    result = service.run()
    assert result.stopped_early is True and len(result.failures) == 3 and result.analyzed == 0


def test_respeita_o_limite():
    service, _, _ = make_service(5)
    result = service.run(limit=2)
    assert result.analyzed == 2 and result.remaining == 3


def test_espera_entre_as_chamadas_mas_nao_depois_da_ultima():
    pauses = []
    service, _, _ = make_service(3, delay_seconds=1.5, sleep=pauses.append)
    service.run()
    assert pauses == [1.5, 1.5]


def test_informa_o_progresso():
    seen = []
    service, _, _ = make_service(2)
    service.run(on_progress=lambda i, n, title: seen.append((i, n, title)))
    assert seen == [(1, 2, "Artigo 1"), (2, 2, "Artigo 2")]