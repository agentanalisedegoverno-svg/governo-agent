"""Carrega os documentos de um caso específico (ETP, edital, cotações etc.)
como content blocks de documento para a Messages API. Diferente do corpus
normativo, esses arquivos variam por caso e não passam pela Files API —
são enviados como base64 diretamente na mensagem.
"""
import base64
from pathlib import Path

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
    for glob in entrada_glob or []:
        caminhos.extend(sorted(caso_dir.glob(glob)))
    if documento_extra:
        caminho_extra = caso_dir / documento_extra
        if caminho_extra.exists() and caminho_extra not in caminhos:
            caminhos.append(caminho_extra)

    blocos = []
    for caminho in caminhos:
        if caminho.is_file():
            bloco = _bloco_de_arquivo(caminho)
            if bloco:
                blocos.append(bloco)
    return blocos
