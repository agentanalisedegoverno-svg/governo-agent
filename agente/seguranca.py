"""Validacoes de entrada para documentos de casos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXTENSOES_DOCUMENTO = {".pdf"}
MAX_DOCUMENTO_BYTES = 20 * 1024 * 1024
MAX_DOCUMENTOS_POR_PROMPT = 25


class EntradaCasoInvalida(ValueError):
    """Entrada de caso ou documento fora dos limites permitidos."""


def resolver_caso(casos_dir: Path, caso_id: str) -> Path:
    if not caso_id or Path(caso_id).name != caso_id or caso_id in {".", ".."}:
        raise EntradaCasoInvalida("Identificador de caso invalido.")
    raiz = casos_dir.resolve()
    caso_dir = (raiz / caso_id).resolve()
    if raiz not in caso_dir.parents:
        raise EntradaCasoInvalida("Caso fora do diretorio permitido.")
    if not caso_dir.is_dir():
        raise EntradaCasoInvalida(f"Caso inexistente: {caso_id}")
    return caso_dir


def resolver_documento(caso_dir: Path, documento: str) -> Path:
    if not documento:
        raise EntradaCasoInvalida("Documento nao informado.")
    relativo = Path(documento)
    if relativo.is_absolute() or any(parte in {"", ".", ".."} for parte in relativo.parts):
        raise EntradaCasoInvalida("Caminho de documento invalido.")
    raiz = caso_dir.resolve()
    caminho = (raiz / relativo).resolve()
    if raiz not in caminho.parents:
        raise EntradaCasoInvalida("Documento fora do caso informado.")
    validar_arquivo_documento(caminho)
    return caminho


def validar_arquivo_documento(caminho: Path) -> None:
    if not caminho.is_file():
        raise EntradaCasoInvalida(f"Documento inexistente: {caminho.name}")
    if caminho.suffix.lower() not in EXTENSOES_DOCUMENTO:
        raise EntradaCasoInvalida(f"Tipo de documento nao suportado: {caminho.suffix}")
    if caminho.stat().st_size > MAX_DOCUMENTO_BYTES:
        raise EntradaCasoInvalida("Documento acima do limite de 20 MB.")


def carregar_caso_json(caso_dir: Path) -> dict[str, Any]:
    caminho = caso_dir / "caso.json"
    if not caminho.exists():
        return {}
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        raise EntradaCasoInvalida("caso.json deve conter um objeto JSON.")
    if "numero_processo" in dados and dados["numero_processo"] != caso_dir.name:
        raise EntradaCasoInvalida("numero_processo diverge do diretorio do caso.")
    if "objeto" in dados and (not isinstance(dados["objeto"], str) or len(dados["objeto"]) < 10):
        raise EntradaCasoInvalida("objeto do caso ausente ou curto demais.")
    return dados

