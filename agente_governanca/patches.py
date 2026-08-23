"""Validacao e aplicacao controlada de patches propostos pelo modelo."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

MAX_PATCHES = 5
MAX_PATCH_BYTES = 120_000
PROTECTED_PREFIXES = (
    ".github/workflows/ai-governor",
    "agente_governanca/",
    "governanca/evidencias/",
)


def caminhos_do_patch(diff: str) -> list[str]:
    caminhos = []
    padroes = (
        r"^diff --git a/(.+) b/(.+)$",
        r"^--- (?:a/)?(.+)$",
        r"^\+\+\+ (?:b/)?(.+)$",
        r"^rename (?:from|to) (.+)$",
    )
    for padrao in padroes:
        for match in re.finditer(padrao, diff, flags=re.MULTILINE):
            for caminho in match.groups():
                caminho = caminho.strip()
                if caminho != "/dev/null" and caminho not in caminhos:
                    caminhos.append(caminho)
    return caminhos


def validar_caminho(caminho: str) -> None:
    if caminho.startswith(('"', "'", "\\")) or "\t" in caminho:
        raise ValueError(f"caminho com escape nao permitido no patch: {caminho}")
    posix = PurePosixPath(caminho)
    if posix.is_absolute() or ".." in posix.parts or ".git" in posix.parts:
        raise ValueError(f"caminho inseguro no patch: {caminho}")
    normalizado = posix.as_posix()
    if normalizado.startswith(PROTECTED_PREFIXES):
        raise ValueError(f"controle protegido contra autoalteracao: {normalizado}")


def validar_patch(diff: str) -> list[str]:
    if not diff.strip().startswith("diff --git "):
        raise ValueError("o patch nao esta em formato unified diff do git")
    if len(diff.encode("utf-8")) > MAX_PATCH_BYTES:
        raise ValueError("patch excede o limite de tamanho")
    if "GIT binary patch" in diff or re.search(r"(?:file )?mode (?:120000|160000)", diff):
        raise ValueError("patch binario, symlink ou submodulo nao e permitido")
    caminhos = caminhos_do_patch(diff)
    if not caminhos:
        raise ValueError("patch sem arquivos de destino")
    for caminho in caminhos:
        validar_caminho(caminho)
    return caminhos


def aplicar_patches(repo: Path, propostas: list[dict]) -> tuple[list[dict], list[dict]]:
    aplicados = []
    rejeitados = []
    for proposta in propostas[:MAX_PATCHES]:
        diff = proposta.get("unified_diff", "")
        try:
            caminhos = validar_patch(diff)
            with tempfile.NamedTemporaryFile("w", suffix=".patch", encoding="utf-8", delete=False) as temp:
                temp.write(diff)
                patch_path = Path(temp.name)
            try:
                subprocess.run(
                    ["git", "-C", str(repo), "apply", "--check", str(patch_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["git", "-C", str(repo), "apply", "--whitespace=fix", str(patch_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            finally:
                patch_path.unlink(missing_ok=True)
            aplicados.append({**proposta, "paths": caminhos})
        except (ValueError, subprocess.CalledProcessError) as exc:
            detalhe = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
            rejeitados.append({"title": proposta.get("title", "Sem titulo"), "reason": detalhe})
    return aplicados, rejeitados
