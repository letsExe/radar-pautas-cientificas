"""Copia os secrets de nível superior para variáveis de ambiente, para o config.py lê-los como no .env."""
from __future__ import annotations

from typing import Mapping, MutableMapping


def export_to_environ(secrets: Mapping, environ: MutableMapping[str, str]) -> list[str]:
    """Exporta só valores simples (texto ou número) e nunca sobrescreve o que já existe.

    Devolve os NOMES exportados (nunca os valores).
    """
    exported: list[str] = []
    for key, value in secrets.items():
        simple = isinstance(value, (str, int, float)) and not isinstance(value, bool)
        if simple and key not in environ:
            environ[key] = str(value)
            exported.append(key)
    return exported