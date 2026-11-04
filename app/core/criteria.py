"""Leitura e validação do criterios.yaml (critérios de noticiabilidade)."""
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "criterios.yaml"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class CriteriaError(ValueError):
    pass


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    description: str
    weight: float
    high_example: str = ""
    low_example: str = ""


@dataclass(frozen=True)
class CriteriaConfig:
    version: str
    highlight_threshold: float
    max_abstract_chars: int
    criteria: tuple[Criterion, ...]
    content_hash: str  # identifica a versão pelo conteúdo
    raw: dict  # cópia fiel do YAML, gravada no banco


def _hash(raw: dict) -> str:
    # Hash do conteúdo, não do texto: comentários e espaços não criam versão nova.
    canonical = json.dumps(raw, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def load_criteria(path: Path = DEFAULT_PATH) -> CriteriaConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

    items = raw.get("criterios")
    if not items:
        raise CriteriaError("O YAML precisa ter a lista 'criterios'.")

    criteria, seen = [], set()
    for item in items:
        try:
            cid = str(item["id"])
            criterion = Criterion(
                id=cid,
                name=str(item["nome"]),
                description=" ".join(str(item["descricao"]).split()),
                weight=float(item["peso"]),
                high_example=str(item.get("nota_alta", "")),
                low_example=str(item.get("nota_baixa", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CriteriaError(f"Critério inválido ({item!r}): {exc!r}") from exc
        if not ID_PATTERN.match(cid):
            raise CriteriaError(f"Id inválido '{cid}': use minúsculas, números e '_'.")
        if cid in seen:
            raise CriteriaError(f"Id de critério repetido: '{cid}'.")
        if criterion.weight <= 0:
            raise CriteriaError(f"O critério '{cid}' precisa ter peso maior que zero.")
        seen.add(cid)
        criteria.append(criterion)

    threshold = float(raw.get("limiar_destaque", 6.5))
    if not 0 <= threshold <= 10:
        raise CriteriaError("'limiar_destaque' deve estar entre 0 e 10.")

    return CriteriaConfig(
        version=str(raw.get("versao", "sem-versao")),
        highlight_threshold=threshold,
        max_abstract_chars=int(raw.get("max_chars_resumo", 3000)),
        criteria=tuple(criteria),
        content_hash=_hash(raw),
        raw=raw,
    )