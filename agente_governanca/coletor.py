"""Coleta um snapshot textual do repositorio sem executar seu conteudo."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

MAX_FILE_BYTES = 180_000
MAX_SNAPSHOT_CHARS = 700_000

IGNORED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}

# O governador local verifica esses caminhos, mas nao envia seu conteudo ao
# modelo de engenharia. O agente documental possui fluxo proprio para os PDFs.
MODEL_CONTENT_EXCLUDED_PREFIXES = ("casos/", "normas/", "governanca/evidencias/")

TEXT_SUFFIXES = {
    "",
    ".c",
    ".cfg",
    ".conf",
    ".cpp",
    ".css",
    ".csv",
    ".dockerfile",
    ".env",
    ".go",
    ".h",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".php",
    ".properties",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".tf",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{16,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*['\"]?([^\s'\"]{12,})"),
]


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def arquivos_rastreados(repo: Path) -> list[str]:
    output = _git(repo, "ls-files", "-z")
    return sorted(path for path in output.split("\0") if path)


def arquivos_alterados(repo: Path, base: str | None, head: str = "HEAD") -> list[str]:
    if not base:
        return arquivos_rastreados(repo)
    output = _git(repo, "diff", "--name-only", "--diff-filter=ACMRT", f"{base}...{head}", check=False)
    return sorted(path for path in output.splitlines() if path)


def eh_texto(caminho: Path) -> bool:
    if caminho.name.lower() in {"dockerfile", "makefile", "procfile"}:
        return True
    return caminho.suffix.lower() in TEXT_SUFFIXES


def ler_texto(caminho: Path) -> str | None:
    try:
        if not caminho.is_file() or caminho.stat().st_size > MAX_FILE_BYTES or not eh_texto(caminho):
            return None
        data = caminho.read_bytes()
        if b"\x00" in data:
            return None
        return data.decode("utf-8", errors="replace")
    except OSError:
        return None


def redigir_secrets(texto: str) -> str:
    redigido = texto
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            redigido = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]", redigido)
        else:
            redigido = pattern.sub("[REDACTED]", redigido)
    return redigido


def montar_snapshot(repo: Path, alterados: list[str]) -> tuple[str, list[str]]:
    rastreados = arquivos_rastreados(repo)
    prioritarios = list(dict.fromkeys(alterados + rastreados))
    blocos: list[str] = []
    incluidos: list[str] = []
    tamanho = 0

    for relativo in prioritarios:
        if relativo.replace("\\", "/").startswith(MODEL_CONTENT_EXCLUDED_PREFIXES):
            continue
        caminho = repo / relativo
        if any(parte in IGNORED_PARTS for parte in caminho.parts):
            continue
        texto = ler_texto(caminho)
        if texto is None:
            continue
        bloco = f"\n<file path=\"{relativo}\">\n{redigir_secrets(texto)}\n</file>\n"
        if tamanho + len(bloco) > MAX_SNAPSHOT_CHARS:
            continue
        blocos.append(bloco)
        incluidos.append(relativo)
        tamanho += len(bloco)

    inventario = "\n".join(rastreados)
    cabecalho = (
        "<repository_inventory>\n"
        + redigir_secrets(inventario)
        + "\n</repository_inventory>\n<repository_files>"
    )
    return cabecalho + "".join(blocos) + "\n</repository_files>", incluidos


def contexto_git(repo: Path) -> dict[str, str]:
    return {
        "sha": _git(repo, "rev-parse", "HEAD"),
        "branch": (
            os.getenv("GITHUB_HEAD_REF")
            or os.getenv("GITHUB_REF_NAME")
            or _git(repo, "branch", "--show-current")
            or "detached"
        ),
        "repository": os.getenv("GITHUB_REPOSITORY", repo.name),
        "actor": os.getenv("GITHUB_ACTOR", "local"),
        "event": os.getenv("GITHUB_EVENT_NAME", "local"),
        "run_id": os.getenv("GITHUB_RUN_ID", "local"),
    }
