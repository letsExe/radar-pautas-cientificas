"""Valida a resposta da LLM e calcula o score final (funções puras, sem rede nem banco)."""
from app.core.criteria import CriteriaConfig
from app.schemas.analysis_schema import ParsedAnalysis

MAX_APPROACHES = 5


class AnalysisError(ValueError):
    """A resposta da LLM (ou o artigo) não permite gerar uma análise válida."""


def _to_score(criterion_id: str, value: object) -> float:
    if isinstance(value, bool):
        raise AnalysisError(f"Nota inválida para '{criterion_id}': {value!r}")
    try:
        score = float(value)
    except (TypeError, ValueError):
        raise AnalysisError(f"Nota inválida para '{criterion_id}': {value!r}") from None
    if not 0 <= score <= 10:  # NaN também é rejeitado aqui
        raise AnalysisError(f"Nota fora da escala 0-10 para '{criterion_id}': {score}")
    return score


def parse_analysis(data: dict, config: CriteriaConfig) -> ParsedAnalysis:
    """Confere se a LLM devolveu exatamente os critérios configurados, com notas válidas."""
    expected = {c.id for c in config.criteria}
    raw_scores = data.get("scores")
    if not isinstance(raw_scores, dict) or set(raw_scores) != expected:
        received = sorted(raw_scores) if isinstance(raw_scores, dict) else raw_scores
        raise AnalysisError(
            f"Critérios devolvidos diferem dos configurados. "
            f"Esperado: {sorted(expected)}; recebido: {received}"
        )
    scores = {cid: _to_score(cid, value) for cid, value in raw_scores.items()}

    raw_just = data.get("justificativas")
    raw_just = raw_just if isinstance(raw_just, dict) else {}
    justifications = {cid: str(raw_just.get(cid, "")).strip() for cid in expected}

    raw_approaches = data.get("enfoques")
    approaches = (
        tuple(a for a in (str(x).strip() for x in raw_approaches) if a)[:MAX_APPROACHES]
        if isinstance(raw_approaches, list)
        else ()
    )

    return ParsedAnalysis(
        scores=scores,
        justifications=justifications,
        general_justification=str(data.get("justificativa_geral") or "").strip(),
        approaches=approaches,
    )


def compute_final_score(scores: dict[str, float], config: CriteriaConfig) -> float:
    """Média ponderada pelos pesos do YAML (calculada pelo sistema, não pela LLM)."""
    total_weight = sum(c.weight for c in config.criteria)
    weighted = sum(scores[c.id] * c.weight for c in config.criteria)
    return round(weighted / total_weight, 2)