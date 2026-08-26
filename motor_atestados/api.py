"""API HTTP do piloto do Motor de Validacao de Atestados."""

from __future__ import annotations

import hmac
import os
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile

from motor_atestados.conhecimento import RepositorioConhecimento
from motor_atestados.excecoes import DocumentoInvalido, ErroMotor, ProvedorIndisponivel
from motor_atestados.extracao import MAX_DOCUMENT_BYTES
from motor_atestados.modelos import (
    EstadoAnalise,
    RegistroAnalise,
    RegistroRevisao,
    RevisaoHumanaEntrada,
    StatusServico,
)
from motor_atestados.provedores import provedores_configurados
from motor_atestados.servico import ServicoAtestados

app = FastAPI(
    title="Motor Governado de Validacao de Atestados",
    version="0.1.0",
    description="Analise assistida por IA com evidencia verificavel e decisao humana.",
)
servico = ServicoAtestados()


def exigir_chave_api(
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    esperada = os.getenv("MOTOR_API_KEY")
    if not esperada:
        raise HTTPException(status_code=503, detail="MOTOR_API_KEY nao configurada.")
    if not x_api_key or not hmac.compare_digest(x_api_key, esperada):
        raise HTTPException(status_code=401, detail="Chave de API invalida.")


async def ler_upload_limitado(documento: UploadFile) -> bytes:
    partes = []
    tamanho = 0
    while bloco := await documento.read(1024 * 1024):
        tamanho += len(bloco)
        if tamanho > MAX_DOCUMENT_BYTES:
            raise DocumentoInvalido(
                f"O PDF deve possuir no maximo {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB."
            )
        partes.append(bloco)
    return b"".join(partes)


@app.get("/health", response_model=StatusServico)
def health() -> StatusServico:
    conhecimento = RepositorioConhecimento()
    return StatusServico(
        provedores_configurados=provedores_configurados(),
        conjuntos_regras=conhecimento.listar_conjuntos(),
    )


@app.get(
    "/v1/rulesets",
    response_model=list[str],
    dependencies=[Depends(exigir_chave_api)],
)
def listar_conjuntos_regras() -> list[str]:
    return RepositorioConhecimento().listar_conjuntos()


@app.post(
    "/v1/analyses",
    response_model=RegistroAnalise,
    status_code=201,
    dependencies=[Depends(exigir_chave_api)],
)
async def criar_analise(
    caso_id: str = Form(...),
    requisito: str = Form(...),
    conjunto_regras_id: str = Form(...),
    provedor: str = Form("auto"),
    provedor_verificador: str | None = Form(None),
    documento: UploadFile = File(...),
) -> RegistroAnalise:
    try:
        conteudo = await ler_upload_limitado(documento)
        return servico.analisar(
            caso_id=caso_id,
            requisito=requisito,
            conjunto_regras_id=conjunto_regras_id,
            documento_nome=documento.filename or "documento.pdf",
            documento=conteudo,
            provedor=provedor,
            provedor_verificador=provedor_verificador or None,
        )
    except ProvedorIndisponivel as exc:
        raise HTTPException(status_code=503, detail={"codigo": exc.codigo, "mensagem": str(exc)})
    except ErroMotor as exc:
        raise HTTPException(status_code=422, detail={"codigo": exc.codigo, "mensagem": str(exc)})


@app.get(
    "/v1/analyses/{analise_id}",
    response_model=EstadoAnalise,
    dependencies=[Depends(exigir_chave_api)],
)
def obter_analise(analise_id: str) -> EstadoAnalise:
    try:
        return servico.obter(analise_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post(
    "/v1/analyses/{analise_id}/reviews",
    response_model=RegistroRevisao,
    status_code=201,
    dependencies=[Depends(exigir_chave_api)],
)
def registrar_revisao(
    analise_id: str, entrada: RevisaoHumanaEntrada
) -> RegistroRevisao:
    try:
        return servico.revisar(analise_id, entrada)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
