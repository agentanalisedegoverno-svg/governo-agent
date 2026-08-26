"""Persistencia local append-only para evidencias e revisoes do piloto."""

from __future__ import annotations

import os
from pathlib import Path

from motor_atestados.modelos import RegistroAnalise, RegistroRevisao

BASE_DADOS = Path(os.getenv("MOTOR_DATA_DIR", ".motor-data"))


class RepositorioAnalises:
    def __init__(self, raiz: Path = BASE_DADOS):
        self.raiz = raiz.resolve()
        self.analises = self.raiz / "analises"
        self.revisoes = self.raiz / "revisoes"

    @staticmethod
    def _validar_id(valor: str) -> None:
        permitido = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
        if not valor or any(c not in permitido for c in valor):
            raise ValueError("Identificador invalido.")

    def salvar_analise(self, registro: RegistroAnalise) -> None:
        self._validar_id(registro.id)
        self.analises.mkdir(parents=True, exist_ok=True)
        destino = self.analises / f"{registro.id}.json"
        if destino.exists():
            raise FileExistsError("Uma analise imutavel com esse ID ja existe.")
        destino.write_text(registro.model_dump_json(indent=2), encoding="utf-8")

    def obter_analise(self, analise_id: str) -> RegistroAnalise:
        self._validar_id(analise_id)
        caminho = self.analises / f"{analise_id}.json"
        if not caminho.is_file():
            raise FileNotFoundError("Analise nao encontrada.")
        return RegistroAnalise.model_validate_json(caminho.read_text(encoding="utf-8"))

    def salvar_revisao(self, revisao: RegistroRevisao) -> None:
        self._validar_id(revisao.analise_id)
        self._validar_id(revisao.id)
        pasta = self.revisoes / revisao.analise_id
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / f"{revisao.id}.json"
        if destino.exists():
            raise FileExistsError("Uma revisao imutavel com esse ID ja existe.")
        destino.write_text(revisao.model_dump_json(indent=2), encoding="utf-8")

    def listar_revisoes(self, analise_id: str) -> list[RegistroRevisao]:
        self._validar_id(analise_id)
        pasta = self.revisoes / analise_id
        if not pasta.exists():
            return []
        return [
            RegistroRevisao.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(pasta.glob("*.json"))
        ]
