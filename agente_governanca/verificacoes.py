"""Verificacoes locais que nao dependem de um modelo de IA."""

from __future__ import annotations

import re
from pathlib import Path

from agente_governanca.coletor import SECRET_PATTERNS, arquivos_rastreados, ler_texto


def _finding(
    finding_id: str,
    title: str,
    category: str,
    severity: str,
    evidence: str,
    recommendation: str,
    files: list[str],
) -> dict:
    return {
        "id": finding_id,
        "title": title,
        "category": category,
        "severity": severity,
        "confidence": "high",
        "evidence": evidence,
        "impact": "O risco pode comprometer confidencialidade, integridade ou auditabilidade do projeto.",
        "recommendation": recommendation,
        "affected_files": files,
        "origin": "deterministic",
    }


def _parece_exemplo(valor: str, caminho: str) -> bool:
    valor = valor.strip("'\"").lower()
    return caminho.endswith((".example", ".sample")) or any(
        marcador in valor
        for marcador in (
            "...",
            "example",
            "changeme",
            "replace_me",
            "<secret>",
            "sua-chave",
            "segredo-local",
            "$env:",
            "${",
            "annotated[",
            "os.getenv(",
            "process.env.",
        )
    )


def verificar_secrets(repo: Path) -> list[dict]:
    achados = []
    reportados: set[tuple[str, int]] = set()
    for relativo in arquivos_rastreados(repo):
        texto = ler_texto(repo / relativo)
        if texto is None:
            continue
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(texto):
                valor = match.group(2) if pattern.groups >= 2 else match.group(0)
                if _parece_exemplo(valor, relativo):
                    continue
                linha = texto.count("\n", 0, match.start()) + 1
                chave = (relativo, linha)
                if chave in reportados:
                    continue
                reportados.add(chave)
                achados.append(
                    _finding(
                        f"DET-SECRET-{len(achados) + 1:03d}",
                        "Possivel secret versionado",
                        "security",
                        "critical",
                        f"Padrao de credencial detectado em {relativo}:{linha}; valor omitido.",
                        "Revogar a credencial, remover seu historico e usar GitHub Secrets ou um cofre de segredos.",
                        [relativo],
                    )
                )
    return achados


def verificar_workflows(repo: Path) -> list[dict]:
    achados = []
    workflow_dir = repo / ".github" / "workflows"
    if not workflow_dir.exists():
        return achados

    for caminho in sorted(workflow_dir.glob("*.y*ml")):
        texto = ler_texto(caminho) or ""
        relativo = caminho.relative_to(repo).as_posix()
        if re.search(r"(?m)^\s*permissions:\s*write-all\s*$", texto):
            achados.append(
                _finding(
                    f"DET-ACTIONS-{len(achados) + 1:03d}",
                    "Permissoes excessivas no GitHub Actions",
                    "security",
                    "high",
                    f"{relativo} declara permissions: write-all.",
                    "Declare somente os escopos necessarios em cada job.",
                    [relativo],
                )
            )
        if "git push" in texto and "ai-governor/" not in texto and "pull request" not in texto.lower():
            achados.append(
                _finding(
                    f"DET-HITL-{len(achados) + 1:03d}",
                    "Workflow pode gravar diretamente na branch atual",
                    "compliance",
                    "high",
                    f"{relativo} contem comando git push sem evidencia de branch governada.",
                    "Envie alteracoes para branch propria e abra Pull Request com aprovacao humana.",
                    [relativo],
                )
            )
    return achados


def executar_verificacoes(repo: Path) -> list[dict]:
    return verificar_secrets(repo) + verificar_workflows(repo)
