"""Validacao deterministica do Knowledge Repository."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


AUTORIDADES = ("policy", "rule", "standard", "template", "knowledge", "example")
STATUS = ("draft", "approved", "deprecated")
TIPOS = ("policy", "rule", "standard", "template", "knowledge", "example", "checklist")
CAMPOS_OBRIGATORIOS = (
    "id",
    "type",
    "domain",
    "status",
    "version",
    "owner",
    "authority",
    "classification",
)


class MetadataInvalida(ValueError):
    """Indica metadata ausente ou inconsistente em artefato de conhecimento."""


@dataclass(frozen=True)
class MetadataConhecimento:
    id: str
    type: str
    domain: str
    status: str
    version: str
    owner: str
    authority: str
    classification: str


def extrair_front_matter(texto: str) -> dict[str, str]:
    if not texto.startswith("---\n"):
        raise MetadataInvalida("front matter ausente")
    fim = texto.find("\n---\n", 4)
    if fim == -1:
        raise MetadataInvalida("front matter sem fechamento")

    metadata: dict[str, str] = {}
    for numero, linha in enumerate(texto[4:fim].splitlines(), start=2):
        if not linha.strip():
            continue
        if ":" not in linha:
            raise MetadataInvalida(f"linha {numero} sem chave YAML simples")
        chave, valor = linha.split(":", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if not chave or not valor:
            raise MetadataInvalida(f"linha {numero} com chave ou valor vazio")
        metadata[chave] = valor
    return metadata


def validar_metadata(metadata: dict[str, str]) -> MetadataConhecimento:
    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS if not metadata.get(campo)]
    if ausentes:
        raise MetadataInvalida(f"campos obrigatorios ausentes: {', '.join(ausentes)}")
    if metadata["status"] not in STATUS:
        raise MetadataInvalida(f"status invalido: {metadata['status']}")
    if metadata["authority"] not in AUTORIDADES:
        raise MetadataInvalida(f"authority invalida: {metadata['authority']}")
    if metadata["type"] not in TIPOS:
        raise MetadataInvalida(f"type invalido: {metadata['type']}")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,95}", metadata["id"]):
        raise MetadataInvalida(f"id invalido: {metadata['id']}")
    return MetadataConhecimento(**{campo: metadata[campo] for campo in CAMPOS_OBRIGATORIOS})


def validar_markdown(caminho: Path) -> MetadataConhecimento:
    return validar_metadata(extrair_front_matter(caminho.read_text(encoding="utf-8")))


def markdowns_de_conhecimento(raiz: Path) -> list[Path]:
    ignorar = {"README.md"}
    return sorted(
        caminho
        for caminho in raiz.rglob("*.md")
        if caminho.name not in ignorar and "__pycache__" not in caminho.parts
    )

