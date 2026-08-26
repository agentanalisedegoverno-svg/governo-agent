"""API HTTP do piloto do Motor de Validacao de Atestados."""

from __future__ import annotations

import hmac
import logging
import os
import re
import time
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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
from motor_atestados.observabilidade import (
    atualizar_contexto,
    configurar_logging,
    iniciar_contexto,
    registrar_evento,
    registrar_falha,
    restaurar_contexto,
)
from motor_atestados.provedores import provedores_configurados
from motor_atestados.servico import ServicoAtestados

logger = configurar_logging()
app = FastAPI(
    title="Motor Governado de Validacao de Atestados",
    version="0.1.0",
    description="Analise assistida por IA com evidencia verificavel e decisao humana.",
)
servico = ServicoAtestados()
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _request_id(request: Request) -> str:
    recebido = request.headers.get("X-Request-ID", "")
    if REQUEST_ID_PATTERN.fullmatch(recebido):
        return recebido
    return str(uuid4())


@app.middleware("http")
async def observar_requisicao(request: Request, call_next):
    request_id = _request_id(request)
    context_handle = iniciar_contexto(
        request_id=request_id,
        stage="http",
        method=request.method,
        path=request.url.path,
    )
    inicio = time.perf_counter()
    inesperada = False
    registrar_evento("http_request_started")
    try:
        try:
            response = await call_next(request)
        except Exception as exc:
            inesperada = True
            registrar_falha(
                "http_request_unhandled_exception",
                exc,
                status_code=500,
                error_code="erro_interno",
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": {
                        "codigo": "erro_interno",
                        "mensagem": "Falha interna. Consulte o log pelo request_id.",
                    }
                },
            )

        duracao = round((time.perf_counter() - inicio) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        if response.status_code >= 400 and not inesperada:
            falha = getattr(request.state, "failure", {})
            registrar_evento(
                "http_request_failed",
                level=logging.ERROR if response.status_code >= 500 else logging.WARNING,
                status_code=response.status_code,
                duration_ms=duracao,
                **falha,
            )
        elif not inesperada:
            registrar_evento(
                "http_request_completed",
                status_code=response.status_code,
                duration_ms=duracao,
            )
        return response
    finally:
        restaurar_contexto(context_handle)


@app.exception_handler(StarletteHTTPException)
async def tratar_erro_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detalhe = exc.detail
    codigo = detalhe.get("codigo") if isinstance(detalhe, dict) else None
    request.state.failure = {
        "error_code": codigo or f"http_{exc.status_code}",
        "error_type": type(exc).__name__,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detalhe},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    atualizar_contexto(stage="request_validation")
    request.state.failure = {
        "error_code": "requisicao_invalida",
        "error_type": type(exc).__name__,
        "validation_error_count": len(exc.errors()),
    }
    detalhes = [
        {"loc": list(item.get("loc", ())), "type": item.get("type", "validation_error")}
        for item in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detalhes})


def exigir_chave_api(
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    atualizar_contexto(stage="authentication")
    esperada = os.getenv("MOTOR_API_KEY")
    if not esperada:
        raise HTTPException(status_code=503, detail="MOTOR_API_KEY nao configurada.")
    if not x_api_key or not hmac.compare_digest(x_api_key, esperada):
        raise HTTPException(status_code=401, detail="Chave de API invalida.")


async def ler_upload_limitado(documento: UploadFile) -> bytes:
    atualizar_contexto(stage="upload")
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
    atualizar_contexto(stage="health_check")
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
    atualizar_contexto(stage="ruleset_list")
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
    atualizar_contexto(
        stage="analysis_request",
        case_id=caso_id,
        ruleset_id=conjunto_regras_id,
        provider=provedor if provedor in {"auto", "anthropic", "openai", "gemini"} else "invalid",
    )
    try:
        conteudo = await ler_upload_limitado(documento)
        atualizar_contexto(document_size_bytes=len(conteudo))
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
    atualizar_contexto(stage="analysis_read", analysis_id=analise_id)
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
    atualizar_contexto(stage="human_review", analysis_id=analise_id)
    try:
        return servico.revisar(analise_id, entrada)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
