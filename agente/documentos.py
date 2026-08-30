"""Carrega os documentos de um caso específico (ETP, edital, cotações etc.)
como content blocks de documento para a Messages API. Diferente do corpus
normativo, esses arquivos variam por caso e não passam pela Files API —
são enviados como base64 diretamente na mensagem.
"""
import base64
from pathlib import Path

from agente.seguranca import (
    EntradaCasoInvalida,
    MAX_DOCUMENTOS_POR_PROMPT,
    resolver_documento,
    validar_arquivo_documento,
)

MEDIA_TYPES_SUPORTADOS = {".pdf": "application/pdf"}


def _bloco_de_arquivo(caminho: Path) -> dict | None:
    media_type = MEDIA_TYPES_SUPORTADOS.get(caminho.suffix.lower())
    if not media_type:
        return None
    dados = base64.standard_b64encode(caminho.read_bytes()).decode("utf-8")
    return {
        "type": "document",
        "source": {"type": "base64", "media_type": media_type, "data": dados},
        "title": caminho.name,
        "citations": {"enabled": True},
    }


def blocos_documento_caso(
    caso_dir: Path, entrada_glob: list[str], documento_extra: str | None = None
) -> list[dict]:
    """Casa entrada_glob contra os arquivos do caso e retorna os blocos de
    documento correspondentes. `documento_extra` permite apontar um arquivo
    específico (usado nas execuções manuais via workflow_dispatch, ex. prompt
    12 - linguagem simples, que não tem um padrão fixo de gatilho).
    """
    caminhos: list[Path] = []
    raiz = caso_dir.resolve()
    for glob in entrada_glob or []:
        if Path(glob).is_absolute() or ".." in Path(glob).parts:
            raise EntradaCasoInvalida(f"Glob de entrada invalido: {glob}")
        for caminho in sorted(caso_dir.glob(glob)):
            resolvido = caminho.resolve()
            if raiz not in resolvido.parents:
                raise EntradaCasoInvalida("Documento fora do caso informado.")
            if resolvido not in caminhos:
                caminhos.append(resolvido)
    if documento_extra:
        caminho_extra = resolver_documento(caso_dir, documento_extra)
        if caminho_extra not in caminhos:
            caminhos.append(caminho_extra)

    if len(caminhos) > MAX_DOCUMENTOS_POR_PROMPT:
        raise EntradaCasoInvalida("Quantidade de documentos acima do limite por prompt.")

    blocos = []
    for caminho in caminhos:
        if caminho.is_file():
            validar_arquivo_documento(caminho)
            bloco = _bloco_de_arquivo(caminho)
            if bloco:
                blocos.append(bloco)
    return blocos
