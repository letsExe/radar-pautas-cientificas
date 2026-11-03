"""Cliente da API do OpenAlex: busca e normaliza os artigos de uma instituição."""
import time
from collections.abc import Iterator

import requests

from app.core.config import settings

BASE_URL = "https://api.openalex.org"

# Pedimos só os campos de que precisamos (resposta menor e mais barata).
FIELDS = ",".join(
    [
        "id",
        "doi",
        "title",
        "display_name",
        "publication_date",
        "type",
        "language",
        "abstract_inverted_index",
        "authorships",
        "primary_location",
        "primary_topic",
    ]
)

RETRY_STATUS = (429, 500, 502, 503, 504)


class OpenAlexError(RuntimeError):
    pass


def _redact(text: str) -> str:
    """Evita que a chave de API vaze em mensagens de erro."""
    key = settings.openalex_api_key
    return text.replace(key, "***") if key else text


def _get(url: str, params: dict, retries: int = 4) -> dict:
    if settings.openalex_api_key:
        params = {**params, "api_key": settings.openalex_api_key}

    last_error = ""
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            last_error = _redact(str(exc))
        else:
            if response.ok:
                return response.json()
            last_error = f"HTTP {response.status_code}: {_redact(response.text[:200])}"
            if response.status_code not in RETRY_STATUS:
                break  # erro nosso (ex.: filtro inválido): tentar de novo não adianta
        time.sleep(2**attempt)
    raise OpenAlexError(f"Falha ao consultar o OpenAlex: {last_error}")


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """O OpenAlex entrega o resumo como {palavra: [posições]}; aqui remontamos o texto."""
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for word, indexes in inverted_index.items():
        for i in indexes:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def _short_id(value: str | None) -> str | None:
    """'https://openalex.org/I165972669' -> 'I165972669'."""
    return value.rstrip("/").split("/")[-1] if value else None


def normalize_work(work: dict, institution_id: str) -> dict:
    """Converte um 'work' do OpenAlex nos campos da tabela articles."""
    target = _short_id(institution_id)

    authors = []
    for authorship in work.get("authorships") or []:
        institutions = authorship.get("institutions") or []
        authors.append(
            {
                "name": (authorship.get("author") or {}).get("display_name"),
                "institutions": [i["display_name"] for i in institutions if i.get("display_name")],
                "unila": any(_short_id(i.get("id")) == target for i in institutions),
            }
        )

    location = work.get("primary_location") or {}
    topic = work.get("primary_topic") or {}
    doi = work.get("doi")

    return {
        "openalex_id": _short_id(work.get("id")),
        "title": work.get("title") or work.get("display_name") or "(sem título)",
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "authors": authors,
        "publication_date": work.get("publication_date"),
        "source_name": (location.get("source") or {}).get("display_name"),
        "doi": doi,
        "url": doi or location.get("landing_page_url"),
        "work_type": work.get("type"),
        "language": work.get("language"),
        "topic": topic.get("display_name"),
        "research_field": (topic.get("field") or {}).get("display_name"),
    }


def fetch_works(
    institution_id: str,
    since: str,
    types: tuple[str, ...] = ("article", "review"),
    per_page: int = 100,
    max_results: int | None = None,
) -> Iterator[dict]:
    """Percorre, página a página, os trabalhos com autoria vinculada à instituição.

    O filtro é pelo ID da instituição (não por texto livre), o que mantém a atribuição estável.
    `since` no formato AAAA-MM-DD.
    """
    filters = [
        f"authorships.institutions.id:{_short_id(institution_id)}",
        f"from_publication_date:{since}",
        "type:" + "|".join(types),
    ]

    cursor = "*"
    delivered = 0
    while cursor:
        data = _get(
            f"{BASE_URL}/works",
            {
                "filter": ",".join(filters),
                "per-page": per_page,
                "cursor": cursor,
                "select": FIELDS,
                "sort": "publication_date:desc",
            },
        )
        for work in data.get("results", []):
            yield normalize_work(work, institution_id)
            delivered += 1
            if max_results and delivered >= max_results:
                return
        cursor = (data.get("meta") or {}).get("next_cursor")