"""Logging estruturado com correlacao e minimizacao de dados."""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

LOGGER_NAME = "motor_atestados"
DEFAULT_LOG_FILE = Path(os.getenv("MOTOR_DATA_DIR", ".motor-data")) / "logs" / "motor.jsonl"

_contexto: ContextVar[dict[str, Any]] = ContextVar("motor_log_context", default={})

_CAMPOS_PERMITIDOS = {
    "request_id",
    "stage",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "error_code",
    "error_type",
    "error_chain",
    "stack",
    "case_id",
    "analysis_id",
    "review_id",
    "ruleset_id",
    "ruleset_version",
    "provider",
    "provider_role",
    "model",
    "document_sha256",
    "document_size_bytes",
    "page_count",
    "input_chars",
    "input_tokens",
    "output_tokens",
    "result",
    "confidence",
    "review_required",
    "alert_count",
    "validation_error_count",
    "configured_providers",
}


def _normalizar_valor(valor: Any) -> Any:
    if isinstance(valor, str):
        return valor.replace("\r", " ").replace("\n", " ")[:256]
    if isinstance(valor, list):
        return [_normalizar_valor(item) for item in valor[:20]]
    if isinstance(valor, dict):
        return {
            str(chave)[:64]: _normalizar_valor(item)
            for chave, item in list(valor.items())[:20]
        }
    if isinstance(valor, (int, float, bool)) or valor is None:
        return valor
    return str(valor)[:256]


class FormatadorJson(logging.Formatter):
    """Serializa somente metadados explicitamente autorizados."""

    def format(self, record: logging.LogRecord) -> str:
        evento = getattr(record, "event", record.getMessage())
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "motor-atestados",
            "environment": os.getenv("MOTOR_ENVIRONMENT", "local"),
            "event": evento,
        }
        for campo in sorted(_CAMPOS_PERMITIDOS):
            valor = getattr(record, campo, None)
            if valor is not None:
                payload[campo] = _normalizar_valor(valor)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def _nivel_configurado() -> int:
    nome = os.getenv("MOTOR_LOG_LEVEL", "INFO").upper()
    return getattr(logging, nome, logging.INFO)


def configurar_logging() -> logging.Logger:
    """Configura stdout e arquivo diario rotativo uma unica vez por processo."""

    logger = logging.getLogger(LOGGER_NAME)
    if getattr(logger, "_motor_configurado", False):
        return logger

    logger.setLevel(_nivel_configurado())
    logger.propagate = False
    formatter = FormatadorJson()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    destino = os.getenv("MOTOR_LOG_FILE", str(DEFAULT_LOG_FILE)).strip()
    if destino and destino.lower() not in {"off", "none", "disabled"}:
        try:
            caminho = Path(destino)
            caminho.parent.mkdir(parents=True, exist_ok=True)
            retencao = max(1, int(os.getenv("MOTOR_LOG_RETENTION_DAYS", "10")))
            arquivo = TimedRotatingFileHandler(
                caminho,
                when="midnight",
                interval=1,
                backupCount=retencao,
                encoding="utf-8",
                utc=True,
            )
            arquivo.setFormatter(formatter)
            logger.addHandler(arquivo)
        except (OSError, ValueError) as exc:
            registrar_falha(
                "logging_file_configuration_failed",
                exc,
                logger=logger,
                level=logging.ERROR,
                stage="startup",
            )

    setattr(logger, "_motor_configurado", True)
    return logger


def iniciar_contexto(**campos: Any) -> Token:
    return _contexto.set({chave: valor for chave, valor in campos.items() if valor is not None})


def atualizar_contexto(**campos: Any) -> None:
    # A tarefa criada pelo middleware herda a mesma referencia. Mutar o mapa
    # permite que a etapa interna volte ao middleware sem misturar requisicoes.
    atual = _contexto.get()
    for chave, valor in campos.items():
        if valor is None:
            atual.pop(chave, None)
        else:
            atual[chave] = valor


def restaurar_contexto(token: Token) -> None:
    _contexto.reset(token)


def contexto_atual() -> dict[str, Any]:
    return dict(_contexto.get())


def registrar_evento(
    evento: str,
    *,
    level: int = logging.INFO,
    logger: logging.Logger | None = None,
    **campos: Any,
) -> None:
    destino = logger or logging.getLogger(LOGGER_NAME)
    metadados = contexto_atual()
    metadados.update(campos)
    extras = {
        "event": evento,
        **{chave: valor for chave, valor in metadados.items() if chave in _CAMPOS_PERMITIDOS},
    }
    destino.log(level, evento, extra=extras)


def _stack_sanitizada(exc: BaseException) -> list[dict[str, Any]]:
    return [
        {
            "file": Path(quadro.filename).name,
            "line": quadro.lineno,
            "function": quadro.name,
        }
        for quadro in traceback.extract_tb(exc.__traceback__)[-12:]
    ]


def _cadeia_tipos(exc: BaseException) -> list[str]:
    tipos = []
    atual: BaseException | None = exc
    while atual is not None and len(tipos) < 5:
        tipos.append(type(atual).__name__)
        atual = atual.__cause__
    return tipos


def registrar_falha(
    evento: str,
    exc: BaseException,
    *,
    level: int = logging.ERROR,
    logger: logging.Logger | None = None,
    **campos: Any,
) -> None:
    registrar_evento(
        evento,
        level=level,
        logger=logger,
        error_type=type(exc).__name__,
        error_chain=_cadeia_tipos(exc),
        stack=_stack_sanitizada(exc),
        **campos,
    )
