"""Carregamento do índice de prompts e substituição de placeholders."""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"


def carregar_indice() -> list[dict]:
    with open(PROMPTS_DIR / "index.json", encoding="utf-8") as f:
        return json.load(f)


def buscar_prompt(indice: list[dict], prompt_id: str) -> dict:
    for prompt in indice:
        if prompt["id"] == prompt_id:
            return prompt
    raise KeyError(f"Prompt '{prompt_id}' não encontrado em prompts/index.json")


def carregar_texto_prompt(prompt_meta: dict, contexto: dict | None = None) -> str:
    """Lê o arquivo .md do prompt e substitui {{CHAVE}} pelos valores de contexto
    (tipicamente vindos de casos/{id}/caso.json). Chaves ausentes permanecem
    literais no texto — o modelo ainda pode inferir a partir dos documentos anexados.
    """
    texto = (PROMPTS_DIR / prompt_meta["arquivo"]).read_text(encoding="utf-8")
    for chave, valor in (contexto or {}).items():
        texto = texto.replace("{{" + chave.upper() + "}}", str(valor))
    return texto
