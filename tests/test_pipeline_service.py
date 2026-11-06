from app.cli import build_parser
from app.services.pipeline_service import PipelineService


class Recorder:
    def __init__(self):
        self.events = []


class FakeSession:
    def __init__(self, recorder):
        self._recorder = recorder

    def commit(self):
        self._recorder.events.append("commit")


class FakeCollection:
    def __init__(self, recorder):
        self._recorder = recorder

    def collect(self, institution_id, since, max_results=None):
        self._recorder.events.append(("collect", institution_id, since, max_results))
        return "COLETA"


class FakeAnalysis:
    def __init__(self, recorder):
        self._recorder = recorder

    def run(self, limit=None, on_progress=None):
        self._recorder.events.append(("analyze", limit))
        return "ANALISE"


def make_pipeline():
    recorder = Recorder()
    pipeline = PipelineService(
        FakeSession(recorder), FakeCollection(recorder), FakeAnalysis(recorder), "I123"
    )
    return pipeline, recorder


def test_coleta_salva_e_so_depois_analisa():
    pipeline, recorder = make_pipeline()
    result = pipeline.run(since="2026-01-01", max_collect=50, analysis_limit=10)
    assert recorder.events == [("collect", "I123", "2026-01-01", 50), "commit", ("analyze", 10)]
    assert result.collection == "COLETA" and result.analysis == "ANALISE"


def test_pular_a_coleta_so_analisa():
    pipeline, recorder = make_pipeline()
    result = pipeline.run(since="2026-01-01", collect=False)
    assert recorder.events == [("analyze", None)]
    assert result.collection is None


def test_cli_valores_padrao():
    args = build_parser().parse_args([])
    assert args.limit == 20 and args.skip_collect is False and args.provider is None
    assert args.since.month == 1 and args.since.day == 1


def test_cli_le_as_opcoes():
    args = build_parser().parse_args(["--since", "2026-03-15", "--limit", "0", "--skip-collect"])
    assert args.since.isoformat() == "2026-03-15" and args.limit == 0 and args.skip_collect