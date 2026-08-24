"""Renderizacao das evidencias de governanca em Markdown."""

from __future__ import annotations

from datetime import datetime, timezone

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _lista(valores: list[str]) -> str:
    return ", ".join(f"`{valor}`" for valor in valores) if valores else "Nao informado"


def renderizar_relatorio(
    resultado: dict,
    contexto: dict,
    incluidos: list[str],
    include_patch_content: bool = True,
) -> str:
    gerado_em = datetime.now(timezone.utc).isoformat()
    status = resultado.get("execution_status", "complete")
    linhas = [
        "<!-- ai-engineering-governor -->",
        "# Evidencia do AI Engineering Governor",
        "",
        f"- Repositorio: `{contexto['repository']}`",
        f"- Commit: `{contexto['sha']}`",
        f"- Branch/ref: `{contexto['branch']}`",
        f"- Evento: `{contexto['event']}`",
        f"- Execucao: `{contexto['run_id']}`",
        f"- Gerado em UTC: `{gerado_em}`",
        f"- Status: **{status}**",
        f"- Risco geral: **{resultado.get('overall_risk', 'unknown')}**",
        f"- Decisao recomendada: **{resultado.get('decision', 'unknown')}**",
        "",
        "## Resumo executivo",
        "",
        resultado.get("summary", "Analise sem resumo."),
        "",
        "## Painel de modelos",
        "",
    ]
    quorum = resultado.get("quorum", {})
    linhas += [
        f"- Quorum minimo: `{quorum.get('minimum', 0)}`",
        f"- Provedores concluidos: `{quorum.get('successful', 0)}`",
        f"- Quorum atingido: `{quorum.get('reached', False)}`",
        "",
    ]
    provider_runs = resultado.get("provider_runs", [])
    if not provider_runs:
        linhas += ["Execucao sem provedores externos.", ""]
    for provider_run in provider_runs:
        if provider_run.get("status") == "success":
            usage = provider_run.get("usage", {})
            linhas.append(
                f"- **{provider_run.get('provider')}**: sucesso com "
                f"`{provider_run.get('model')}` "
                f"(entrada `{usage.get('input_tokens', 0)}`, saida `{usage.get('output_tokens', 0)}` tokens)"
            )
        else:
            linhas.append(
                f"- **{provider_run.get('provider')}**: falha "
                f"`{provider_run.get('error_type')}` - {provider_run.get('message')}"
            )
    if provider_runs:
        linhas.append("")

    findings = sorted(
        resultado.get("findings", []),
        key=lambda item: SEVERITY_ORDER.get(item.get("severity", "info"), 9),
    )
    linhas += ["## Riscos e recomendacoes", ""]
    if not findings:
        linhas += ["Nenhum achado foi registrado nesta execucao.", ""]
    for finding in findings:
        linhas += [
            f"### {finding.get('id', 'SEM-ID')} - {finding.get('title', 'Sem titulo')}",
            "",
            f"- Severidade: **{finding.get('severity', 'info')}**",
            f"- Categoria: `{finding.get('category', 'unknown')}`",
            f"- Confianca: `{finding.get('confidence', 'unknown')}`",
            f"- Origem: `{finding.get('origin', 'ai')}`",
            f"- Arquivos: {_lista(finding.get('affected_files', []))}",
            "",
            f"**Evidencia:** {finding.get('evidence', '')}",
            "",
            f"**Impacto:** {finding.get('impact', '')}",
            "",
            f"**Recomendacao:** {finding.get('recommendation', '')}",
            "",
        ]

    linhas += ["## Decisoes arquiteturais propostas", ""]
    decisoes = resultado.get("architecture_decisions", [])
    if not decisoes:
        linhas += ["Nenhuma ADR foi proposta.", ""]
    for adr in decisoes:
        linhas += [
            f"### {adr.get('title', 'Sem titulo')}",
            "",
            f"- Status: `{adr.get('status', 'proposed')}`",
            f"- Contexto: {adr.get('context', '')}",
            f"- Decisao: {adr.get('decision', '')}",
            f"- Consequencias: {adr.get('consequences', '')}",
            "",
        ]

    linhas += ["## Continuous Knowledge Pull", ""]
    atualizacoes = resultado.get("knowledge_updates", [])
    if not atualizacoes:
        linhas += ["Nenhuma mudanca externa relevante foi confirmada nesta execucao.", ""]
    for atualizacao in atualizacoes:
        linhas += [
            f"### {atualizacao.get('title', 'Sem titulo')}",
            "",
            f"- Regra atual: {atualizacao.get('current_rule', '')}",
            f"- Mudanca externa: {atualizacao.get('external_change', '')}",
            f"- Impacto: {atualizacao.get('impact', '')}",
            f"- Politica candidata: `{atualizacao.get('recommended_policy_file', '')}`",
            f"- Fontes: {'; '.join(atualizacao.get('sources', [])) or 'Nao informadas'}",
            "",
        ]

    linhas += ["## Alteracoes propostas", ""]
    propostas = resultado.get("proposed_patches", [])
    if not propostas:
        linhas += ["Nenhum patch foi proposto.", ""]
    for proposta in propostas:
        linhas += [
            f"### {proposta.get('title', 'Sem titulo')}",
            "",
            proposta.get("rationale", ""),
            "",
        ]
        if include_patch_content:
            linhas += [
                "<details><summary>Patch proposto</summary>",
                "",
                "```diff",
                proposta.get("unified_diff", ""),
                "```",
                "",
                "</details>",
                "",
            ]

    aplicados = resultado.get("applied_patches", [])
    rejeitados = resultado.get("rejected_patches", [])
    linhas += [
        "## Controles de execucao",
        "",
        f"- Arquivos textuais considerados: `{len(incluidos)}`",
        f"- Patches validados e aplicados na branch de trabalho: `{len(aplicados)}`",
        f"- Patches rejeitados pelos controles: `{len(rejeitados)}`",
        f"- Atualizacoes externas rejeitadas por fonte: `{len(resultado.get('rejected_knowledge_updates', []))}`",
        "- Merge ou aprovacao automatica: `proibido`",
        "- Alteracoes na branch protegida: `proibido`",
        "",
    ]
    for rejeitado in rejeitados:
        linhas.append(f"- Patch rejeitado `{rejeitado['title']}`: {rejeitado['reason']}")
    if rejeitados:
        linhas.append("")

    linhas += [
        "---",
        "Esta evidencia e uma recomendacao tecnica sujeita a revisao humana. "
        "Ela nao autoriza merge, deploy ou alteracao de politica.",
        "",
    ]
    return "\n".join(linhas)
