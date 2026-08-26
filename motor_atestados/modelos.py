"""Contratos de dominio e de API do motor de atestados."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ModeloEstrito(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResultadoAnalise(str, Enum):
    ATENDE = "ATENDE"
    ATENDE_PARCIALMENTE = "ATENDE_PARCIALMENTE"
    NAO_ATENDE = "NAO_ATENDE"
    REVISAO_HUMANA = "REVISAO_HUMANA"
    ERRO_PROCESSAMENTO = "ERRO_PROCESSAMENTO"


class NivelConfianca(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class StatusCriterio(str, Enum):
    ATENDIDO = "ATENDIDO"
    PARCIAL = "PARCIAL"
    NAO_ATENDIDO = "NAO_ATENDIDO"
    AMBIGUO = "AMBIGUO"


class CriterioRegra(ModeloEstrito):
    id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{2,63}$")
    descricao: str = Field(min_length=3, max_length=500)
    obrigatorio: bool = True
    termos_aceitos: list[str] = Field(default_factory=list)
    termos_insuficientes: list[str] = Field(default_factory=list)
    orientacao: str = Field(default="", max_length=2_000)


class ConjuntoRegras(ModeloEstrito):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    titulo: str
    versao: str
    vigente_desde: str
    fonte: str
    template: str
    instructions: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    criterios: list[CriterioRegra] = Field(min_length=1)


class PaginaDocumento(ModeloEstrito):
    numero: int = Field(ge=1)
    texto: str


class DocumentoExtraido(ModeloEstrito):
    nome: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mime_type: Literal["application/pdf"] = "application/pdf"
    paginas: list[PaginaDocumento] = Field(min_length=1)


class Evidencia(ModeloEstrito):
    pagina: int = Field(ge=1)
    trecho: str = Field(min_length=1, max_length=4_000)
    criterios: list[str] = Field(min_length=1)
    verificada: bool = False
    origem: Literal["regra", "ia"] = "ia"


class AvaliacaoCriterio(ModeloEstrito):
    criterio_id: str
    status: StatusCriterio
    justificativa: str = Field(min_length=1, max_length=4_000)


class ParecerProvedor(ModeloEstrito):
    resultado: ResultadoAnalise
    confianca: NivelConfianca
    criterios: list[AvaliacaoCriterio]
    evidencias: list[Evidencia]
    justificativa: str = Field(min_length=1, max_length=8_000)


class ExecucaoProvedor(ModeloEstrito):
    provedor: str
    modelo: str
    papel: Literal["primario", "verificador"]
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)


class RegistroAnalise(ModeloEstrito):
    id: str
    caso_id: str
    requisito: str
    conjunto_regras_id: str
    conjunto_regras_versao: str
    documento_nome: str
    documento_sha256: str
    resultado: ResultadoAnalise
    confianca: NivelConfianca
    criterios: list[AvaliacaoCriterio]
    evidencias: list[Evidencia]
    justificativa: str
    revisao_humana_obrigatoria: bool
    alertas: list[str] = Field(default_factory=list)
    provedores: list[ExecucaoProvedor] = Field(default_factory=list)
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RevisaoHumanaEntrada(ModeloEstrito):
    decisao: ResultadoAnalise
    revisor: str = Field(min_length=3, max_length=200)
    justificativa: str = Field(min_length=10, max_length=8_000)


class RegistroRevisao(RevisaoHumanaEntrada):
    id: str
    analise_id: str
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EstadoAnalise(ModeloEstrito):
    analise: RegistroAnalise
    revisoes: list[RegistroRevisao]


class StatusServico(ModeloEstrito):
    status: Literal["ok"] = "ok"
    provedores_configurados: list[str]
    conjuntos_regras: list[str]
