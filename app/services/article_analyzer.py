from app.core.criteria import CriteriaConfig
from app.core.llm import LLMClient
from app.models import Article
from app.schemas.analysis_schema import AnalysisResult
from app.services.analysis_validator import AnalysisError, compute_final_score, parse_analysis
from app.services.prompt_builder import build_prompt


class ArticleAnalyzer:
    """Analisa o potencial de noticiabilidade de um artigo usando uma LLM."""

    def __init__(self, llm: LLMClient, config: CriteriaConfig) -> None:
        self._llm = llm
        self._config = config

    def analyze(self, article: Article) -> AnalysisResult:
        if not (article.abstract or "").strip():
            raise AnalysisError("O artigo não tem resumo; não há o que analisar.")

        response = self._llm.generate_json(build_prompt(self._config, article))
        parsed = parse_analysis(response.data, self._config)
        final_score = compute_final_score(parsed.scores, self._config)

        return AnalysisResult(
            scores=parsed.scores,
            justifications=parsed.justifications,
            general_justification=parsed.general_justification,
            approaches=parsed.approaches,
            final_score=final_score,
            recommended=final_score >= self._config.highlight_threshold,
            model=response.model,
        )