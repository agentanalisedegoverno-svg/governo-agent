"""Carregamento controlado do conhecimento versionado do negocio."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from motor_atestados.excecoes import ConhecimentoInvalido
from motor_atestados.modelos import ConjuntoRegras

BASE_CONHECIMENTO = Path(__file__).resolve().parent.parent / "conhecimento"


class RepositorioConhecimento:
    def __init__(self, raiz: Path = BASE_CONHECIMENTO):
        self.raiz = raiz.resolve()

    def listar_conjuntos(self) -> list[str]:
        return sorted(path.stem for path in (self.raiz / "regras").glob("*.json"))

    def carregar_conjunto(self, conjunto_id: str) -> ConjuntoRegras:
        if not conjunto_id or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in conjunto_id):
            raise ConhecimentoInvalido("Identificador de conjunto de regras invalido.")
        caminho = self.raiz / "regras" / f"{conjunto_id}.json"
        if not caminho.is_file():
            raise ConhecimentoInvalido(f"Conjunto de regras inexistente: {conjunto_id}")
        try:
            conjunto = ConjuntoRegras.model_validate_json(caminho.read_text(encoding="utf-8"))
        except (OSError, ValidationError, json.JSONDecodeError) as exc:
            raise ConhecimentoInvalido(f"Conjunto de regras invalido: {conjunto_id}") from exc
        if conjunto.id != conjunto_id:
            raise ConhecimentoInvalido("O ID interno diverge do nome do conjunto de regras.")
        self._validar_referencias(conjunto)
        return conjunto

    def _ler_markdown(self, pasta: str, nome: str) -> str:
        if Path(nome).name != nome or not nome.endswith(".md"):
            raise ConhecimentoInvalido(f"Referencia de conhecimento invalida: {nome}")
        caminho = self.raiz / pasta / nome
        if not caminho.is_file():
            raise ConhecimentoInvalido(f"Arquivo de conhecimento ausente: {pasta}/{nome}")
        return caminho.read_text(encoding="utf-8")

    def _validar_referencias(self, conjunto: ConjuntoRegras) -> None:
        self._ler_markdown("templates", conjunto.template)
        for nome in conjunto.instructions:
            self._ler_markdown("instructions", nome)
        for nome in conjunto.skills:
            self._ler_markdown("skills", nome)

    def montar_instrucao(self, conjunto: ConjuntoRegras) -> str:
        blocos = [self._ler_markdown("templates", conjunto.template)]
        blocos.extend(self._ler_markdown("instructions", nome) for nome in conjunto.instructions)
        blocos.extend(self._ler_markdown("skills", nome) for nome in conjunto.skills)
        return "\n\n---\n\n".join(blocos)
