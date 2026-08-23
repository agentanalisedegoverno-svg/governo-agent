"""Ponto de entrada chamado pelo GitHub Actions (ou localmente) para rodar as
análises aplicáveis. Duas formas de disparo:

  - Automática: `--arquivos` recebe a lista de arquivos alterados (um por
    linha); o script casa cada arquivo contra `entrada_glob` dos prompts com
    `auto_trigger: true` em prompts/index.json.
  - Manual: `--caso` + `--prompt` (e opcionalmente `--documento`) forçam a
    execução de um prompt específico, incluindo os marcados como
    `auto_trigger: false` (ex.: contradições normativas, linguagem simples).
"""
import argparse
import fnmatch
import json
import os
from pathlib import Path

import anthropic

from agente.documentos import blocos_documento_caso
from agente.normas import blocos_normas, garantir_normas_atualizadas
from agente.prompts import buscar_prompt, carregar_indice, carregar_texto_prompt

BASE_DIR = Path(__file__).resolve().parent.parent
CASOS_DIR = BASE_DIR / "casos"
MODELO_PADRAO = "claude-opus-5"

SYSTEM_FIXO = (
    "Você está operando dentro de um pipeline automatizado de análise de "
    "processos de contratação pública brasileiros, regidos pela Lei 14.133/2021 "
    "e normas correlatas. Sempre cite trechos e a página exata das fontes "
    "fornecidas. Sinalize claramente quando uma conclusão depender de "
    "informação ausente nos documentos anexados."
)


def _identificar_tarefas_automaticas(indice: list[dict], arquivos_alterados: list[str]):
    """Retorna {(caso_id, prompt_id): prompt_meta} para arquivos sob casos/**
    que casam com o entrada_glob de algum prompt com auto_trigger=true."""
    tarefas: dict[tuple[str, str], dict] = {}
    for caminho in arquivos_alterados:
        partes = Path(caminho).parts
        if len(partes) < 3 or partes[0] != "casos":
            continue
        caso_id = partes[1]
        relativo = "/".join(partes[2:])
        for prompt in indice:
            if not prompt.get("auto_trigger", False):
                continue
            for glob in prompt.get("entrada_glob") or []:
                if fnmatch.fnmatch(relativo, glob):
                    tarefas[(caso_id, prompt["id"])] = prompt
                    break
    return tarefas


def _carregar_metadados_caso(caso_id: str) -> dict:
    caminho = CASOS_DIR / caso_id / "caso.json"
    if caminho.exists():
        return json.loads(caminho.read_text(encoding="utf-8"))
    return {}


def _montar_conteudo_usuario(
    manifest_normas: dict, docs_caso: list[dict], instrucao: str
) -> list[dict]:
    conteudo = list(blocos_normas(manifest_normas))
    if docs_caso:
        docs_caso = list(docs_caso)
        docs_caso[-1] = {**docs_caso[-1], "cache_control": {"type": "ephemeral"}}
        conteudo.extend(docs_caso)
    conteudo.append({"type": "text", "text": instrucao})
    return conteudo


def executar_prompt(
    client: anthropic.Anthropic,
    indice: list[dict],
    manifest_normas: dict,
    caso_id: str,
    prompt_id: str,
    documento_extra: str | None = None,
):
    prompt_meta = buscar_prompt(indice, prompt_id)
    if not prompt_meta.get("automatizavel", True):
        print(
            f"[aviso] '{prompt_id}' não é automatizável via API "
            f"({prompt_meta.get('motivo_manual', 'uso manual no NotebookLM')}) — pulando."
        )
        return None

    metadados = _carregar_metadados_caso(caso_id)
    instrucao = carregar_texto_prompt(prompt_meta, contexto=metadados)
    docs_caso = blocos_documento_caso(
        CASOS_DIR / caso_id, prompt_meta.get("entrada_glob"), documento_extra
    )
    conteudo = _montar_conteudo_usuario(manifest_normas, docs_caso, instrucao)

    modelo = prompt_meta.get("modelo") or MODELO_PADRAO
    resposta = client.beta.messages.create(
        model=modelo,
        max_tokens=16000,
        system=SYSTEM_FIXO,
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": conteudo}],
        betas=["files-api-2025-04-14"],
    )
    return prompt_meta, resposta


def _renderizar_relatorio(prompt_meta: dict, resposta) -> str:
    linhas = [f"# {prompt_meta['titulo']}", ""]
    for bloco in resposta.content:
        if bloco.type == "text":
            linhas.append(bloco.text)
    uso = resposta.usage
    linhas += [
        "",
        "---",
        f"_Gerado por `{resposta.model}` — "
        f"entrada: {uso.input_tokens} tokens plenos, "
        f"{uso.cache_read_input_tokens} lidos do cache, "
        f"{uso.cache_creation_input_tokens} escritos no cache._",
    ]
    return "\n".join(linhas)


def _gravar_relatorio(caso_id: str, prompt_id: str, conteudo: str) -> Path:
    saida_dir = CASOS_DIR / caso_id / "analises"
    saida_dir.mkdir(parents=True, exist_ok=True)
    saida_path = saida_dir / f"{prompt_id}.md"
    saida_path.write_text(conteudo, encoding="utf-8")
    return saida_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arquivos", default="", help="Arquivos alterados, um por linha")
    parser.add_argument("--caso", help="Execução manual: ID do processo em casos/")
    parser.add_argument("--prompt", help="Execução manual: ID do prompt em prompts/index.json")
    parser.add_argument("--documento", help="Execução manual: arquivo específico dentro do caso")
    args = parser.parse_args()

    indice = carregar_indice()
    client = anthropic.Anthropic()
    manifest_normas = garantir_normas_atualizadas(client)

    if args.caso and args.prompt:
        tarefas = {(args.caso, args.prompt): None}
    else:
        arquivos = [linha.strip() for linha in args.arquivos.splitlines() if linha.strip()]
        tarefas = _identificar_tarefas_automaticas(indice, arquivos)

    if not tarefas:
        print("Nenhum prompt aplicável para os arquivos alterados.")
        return

    resumo = ["## Análises geradas"]
    for caso_id, prompt_id in tarefas:
        print(f"[executando] caso={caso_id} prompt={prompt_id}")
        resultado = executar_prompt(
            client, indice, manifest_normas, caso_id, prompt_id, args.documento
        )
        if resultado is None:
            continue
        prompt_meta, resposta = resultado
        relatorio = _renderizar_relatorio(prompt_meta, resposta)
        saida_path = _gravar_relatorio(caso_id, prompt_id, relatorio)
        print(f"[gravado] {saida_path}")
        resumo.append(f"- **{caso_id} / {prompt_meta['titulo']}** → `{saida_path.relative_to(BASE_DIR)}`")

    resumo_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo_path:
        with open(resumo_path, "a", encoding="utf-8") as f:
            f.write("\n".join(resumo) + "\n")
    else:
        print("\n".join(resumo))


if __name__ == "__main__":
    main()
