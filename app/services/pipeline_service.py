"""Orquestra o fluxo completo: coletar artigos e analisar os pendentes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.services.analysis_service import (
        AnalysisRunResult,
        AnalysisService,
        ProgressCallback,
    )
    from app.services.collection_service import CollectionResult, CollectionService


@dataclass(frozen=True)
class PipelineResult:
    collection: CollectionResult | None  # None quando a coleta foi pulada
    analysis: AnalysisRunResult


class PipelineService:
    """Ponto único de entrada do fluxo: usado pelo terminal e, depois, pela interface."""

    def __init__(
        self,
        session: Session,
        collection_service: CollectionService,
        analysis_service: AnalysisService,
        institution_id: str,
    ) -> None:
        self._session = session
        self._collection_service = collection_service
        self._analysis_service = analysis_service
        self._institution_id = institution_id

    def run(
        self,
        since: str,
        collect: bool = True,
        max_collect: int | None = None,
        analysis_limit: int | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> PipelineResult:
        collection = None
        if collect:
            collection = self._collection_service.collect(self._institution_id, since, max_collect)
            self._session.commit()  # os artigos ficam salvos antes de gastar chamadas à LLM
        analysis = self._analysis_service.run(limit=analysis_limit, on_progress=on_progress)
        return PipelineResult(collection=collection, analysis=analysis)