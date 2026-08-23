"""Mantém o corpus normativo fixo (Lei 14.133/2021 e correlatas) sincronizado
com a Files API da Anthropic, reaproveitando file_id via um manifesto versionado
em normas/manifest.json — evita reenviar os PDFs quando eles não mudaram e
permite marcar o bloco com cache_control para reaproveitar o processamento
entre as 13 análises.
"""
import hashlib
import json
from pathlib import Path

NORMAS_DIR = Path(__file__).resolve().parent.parent / "normas"
MANIFEST_PATH = NORMAS_DIR / "manifest.json"


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _carregar_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def _salvar_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def garantir_normas_atualizadas(client) -> dict:
    """Sobe para a Files API qualquer PDF em normas/ cujo conteúdo tenha mudado
    desde o último manifesto. Retorna {nome_arquivo: {file_id, sha256}}.
    """
    manifest = _carregar_manifest()
    alterado = False
    for caminho in sorted(NORMAS_DIR.glob("*.pdf")):
        nome = caminho.name
        checksum = _sha256(caminho)
        entrada = manifest.get(nome)
        if entrada and entrada.get("sha256") == checksum:
            continue
        with open(caminho, "rb") as f:
            enviado = client.beta.files.upload(file=(nome, f, "application/pdf"))
        manifest[nome] = {"file_id": enviado.id, "sha256": checksum}
        alterado = True
        print(f"[normas] enviado {nome} -> {enviado.id}")
    if alterado:
        _salvar_manifest(manifest)
    return manifest


def blocos_normas(manifest: dict) -> list[dict]:
    """Gera os content blocks de documento para o corpus normativo. O último
    bloco recebe cache_control — tudo até ele forma um prefixo estável e
    reaproveitável entre as chamadas de todos os 13 prompts.
    """
    nomes = sorted(manifest.keys())
    blocos = []
    for i, nome in enumerate(nomes):
        bloco = {
            "type": "document",
            "source": {"type": "file", "file_id": manifest[nome]["file_id"]},
            "title": nome,
        }
        if i == len(nomes) - 1:
            bloco["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
        blocos.append(bloco)
    return blocos
