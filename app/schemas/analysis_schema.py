from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedAnalysis:
    """Resposta da LLM já validada."""

    scores: dict[str, float]
    justifications: dict[str, str]
    general_justification: str
    approaches: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisResult:
    """Resultado completo da análise de um artigo, pronto para ser gravado."""

    scores: dict[str, float]
    justifications: dict[str, str]
    general_justification: str
    approaches: tuple[str, ...]
    final_score: float
    recommended: bool
    model: str