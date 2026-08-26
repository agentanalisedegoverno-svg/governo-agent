# licitacoes-agent

Para configurar o repositório e executar uma avaliação guiada com o time, consulte
o [Manual de Uso](MANUAL_DE_USO.md).

O primeiro recorte do **Motor Governado de Validação de Atestados** está em
`motor_atestados/`. Consulte o [manual do motor](MANUAL_MOTOR_ATESTADOS.md) e a
[especificação da massa de testes](MASSA_TESTES_PRODUTO.md).

Agente automatizado de análise de processos de contratação pública brasileiros
(Lei 14.133/2021), orquestrado via GitHub Actions. Cada documento adicionado a
um caso dispara automaticamente as análises aplicáveis via API da Claude —
sem colar prompt manualmente em nenhuma interface.

## Como funciona

```
push em main/casos/** →  Action detecta quais arquivos mudaram
                     →  casa contra entrada_glob de prompts/index.json
                     →  chama a API da Claude uma vez por prompt aplicável
                     →  grava casos/{id}/analises/{prompt}.md
                     →  abre PR (push) ou comenta na PR existente
```

Não é um agente com loop de tool-use — é orquestração determinística (o
GitHub Actions decide o que roda) + chamadas simples à Messages API, uma por
prompt. Isso é intencional: cada análise fica auditável e reproduzível, o que
importa em contexto de compliance.

## Estrutura

- `normas/` — corpus jurídico fixo (Lei 14.133, Decreto 11.462, IN 65/2021,
  Lei 15.263 etc.). Adicione os PDFs oficiais aqui — ver `normas/README.md`.
- `prompts/index.json` — mapa de qual prompt roda para qual padrão de arquivo
  (`entrada_glob`) e se dispara automaticamente (`auto_trigger`) ou só sob
  demanda.
- `prompts/*.md` — os 13 prompts especializados, com placeholders `{{OBJETO}}`,
  `{{TEMA}}` etc. preenchidos a partir de `casos/{id}/caso.json`.
- `casos/{numero-processo}/` — documentos de cada processo real; ver
  `casos/EXEMPLO-001/LEIA-ME.md` para a convenção de nomes.
- `agente/` — o script Python que a Action executa.

## Rodando localmente

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha ANTHROPIC_API_KEY
export $(cat .env | xargs)

python -m agente.executar --caso EXEMPLO-001 --prompt revisao-etp
```

## Custo e cache

O corpus em `normas/` é enviado uma vez via Files API (reaproveitado por
checksum em `normas/manifest.json`) e referenciado com `cache_control` em
todas as chamadas — ele é o mesmo bloco de conteúdo nas 13 análises, então só
a primeira paga o preço cheio de processamento; as seguintes leem do cache
(~10% do custo). Os documentos do caso ganham um segundo breakpoint, então
quando dois prompts disparam pelo mesmo arquivo (ex. `etp.*` aciona revisão de
ETP + matriz de riscos), o documento também é reaproveitado entre as duas
chamadas.

Modelo padrão: `claude-opus-5`. Dá para sobrescrever por prompt com o campo
`"modelo"` em `prompts/index.json` se quiser usar um modelo mais barato em
prompts de menor risco (ex. FAQ, linguagem simples).

## Segurança

- **Este repositório precisa ser privado** — os documentos de caso (ETPs,
  cotações, propostas) são sensíveis/protegidos por sigilo até a publicação.
- `ANTHROPIC_API_KEY` como GitHub Secret (`Settings → Secrets and variables →
  Actions`).
- O workflow documental com secret roda apenas em `main` ou manualmente. Em PR,
  o governador usa seu código confiável e nunca executa o conteúdo proposto.

## AI Engineering Governor

O repositório também contém um governador de engenharia permanente e separado
do agente de licitações. Ele avalia software, arquitetura, IA, infraestrutura,
segurança, privacidade e governança de dados.

O governador usa um painel independente com Claude, modelos GPT pela OpenAI API
e Gemini. Por padrão, ao menos dois provedores precisam concluir a análise. A
indisponibilidade de um provedor não apaga os achados dos demais, e a consolidação
sempre preserva a maior severidade.

O fluxo possui separação de privilégios:

```text
push em qualquer branch -> verificações determinísticas, token somente leitura
Pull Request             -> governador confiável analisa a proposta como dados
push em main             -> análise completa e proposta em branch ai-governor/*
segunda-feira, 08:17 UTC -> Continuous Knowledge Pull em fontes autorizadas
```

Nenhuma alteração é aplicada diretamente em `main`. Evidências e patches são
enviados a uma branch própria e viram Pull Request sujeito à aprovação humana.
O código da PR não é executado pelo governador privilegiado.

As políticas e a memória operacional ficam em `governanca/`. O ponto de entrada
local é:

```bash
python -m agente_governanca --mode deterministic
python -m agente_governanca --require-ai
python -m agente_governanca --knowledge-pull --apply-proposals
```

Para ativar a análise por IA, cadastre `ANTHROPIC_API_KEY` em
`Settings > Secrets and variables > Actions`, junto com `OPENAI_API_KEY` e
`GEMINI_API_KEY`. Em `Settings > Actions > General`,
habilite **Allow GitHub Actions to create and approve pull requests**; o workflow
somente cria PRs e não usa a permissão para aprová-los.

Proteja `main` com ruleset exigindo Pull Request, ao menos uma aprovação humana,
revisão de CODEOWNER e invalidação de aprovações quando houver novos commits.

## Limitações conhecidas

- **Prompt 11 (podcast educativo)** usa o recurso de Audio Overview do
  NotebookLM, que não tem equivalente na API da Claude — continua sendo uso
  manual, copiado para a interface do NotebookLM.
- **Prompts 06 e 12** não têm um documento-gatilho fixo e só rodam via
  `workflow_dispatch` manual.
- A saída da IA é insumo de análise, não substitui parecer jurídico formal —
  isso está registrado como aviso em vários dos prompts.
