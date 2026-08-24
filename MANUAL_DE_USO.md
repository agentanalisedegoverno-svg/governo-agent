# Manual de Uso e Avaliação

## 1. Finalidade

Este manual orienta a configuração, operação e avaliação controlada do
`licitacoes-agent`. O repositório contém dois componentes distintos:

1. **Agente de licitações:** analisa documentos de contratações públicas e gera
   relatórios em Markdown. Atualmente usa a API Claude/Anthropic.
2. **AI Engineering Governor:** avalia continuamente código, arquitetura,
   infraestrutura, segurança, IA, privacidade e governança. Usa um painel
   independente com Claude, GPT/OpenAI e Gemini.

Nenhum dos componentes substitui decisão administrativa, técnica ou jurídica.
Toda alteração proposta pelo sistema deve passar por Pull Request e aprovação
humana.

## 2. Regras para a avaliação inicial

- Mantenha o repositório **privado**.
- Use somente casos sintéticos ou documentos públicos na primeira avaliação.
- Não inclua CPF, dados bancários, propostas sigilosas, credenciais ou dados
  pessoais reais.
- Nunca grave chaves em arquivos versionados, issues, comentários ou logs.
- Não permita merge automático de Pull Requests criados pelos agentes.
- Confirme custos, retenção e tratamento de dados de cada provedor antes de usar
  documentos reais.

## 3. Perfis envolvidos

| Perfil | Responsabilidade |
| --- | --- |
| Administrador do repositório | Configurar secrets, Actions, permissões e proteção de `main` |
| Avaliador técnico | Executar os cenários, revisar logs, evidências, código e arquitetura |
| Avaliador de segurança e dados | Verificar exposição, classificação, retenção e controles de acesso |
| Avaliador jurídico ou de negócio | Validar citações, ressalvas e utilidade dos relatórios de licitação |
| Aprovador humano | Decidir sobre merge, exceções, políticas e mudanças propostas |

Uma mesma pessoa pode exercer mais de um perfil durante o piloto, mas a aprovação
final não deve ser delegada ao agente.

## 4. Pré-requisitos

### 4.1 GitHub

- Acesso administrativo ao repositório.
- GitHub Actions habilitado.
- Permissão para criar secrets do repositório.
- Permissão para configurar rulesets ou branch protection, quando disponível no
  plano GitHub utilizado.

### 4.2 Execução local

- Git.
- Python 3.12.
- `pip` e suporte a ambiente virtual.
- WSL, Linux, macOS ou PowerShell no Windows.

### 4.3 Provedores de IA

- Chave da Anthropic para Claude.
- Chave da OpenAI com faturamento e cota de API ativos.
- Chave da Gemini API.

Uma assinatura do ChatGPT não habilita automaticamente créditos para a OpenAI
API. A API possui chave, limites e faturamento próprios.

## 5. Configuração do GitHub

### 5.1 Cadastrar os secrets

No repositório, acesse:

`Settings > Secrets and variables > Actions > New repository secret`

Cadastre:

| Secret | Utilização |
| --- | --- |
| `ANTHROPIC_API_KEY` | Agente de licitações e painel do governador |
| `OPENAI_API_KEY` | Painel do governador |
| `GEMINI_API_KEY` | Painel do governador |

Depois de salvar, o GitHub mostra apenas o nome do secret. O valor não deve ser
recuperado ou impresso por workflows.

### 5.2 Permitir Pull Requests do GitHub Actions

Acesse `Settings > Actions > General` e configure:

1. Em **Workflow permissions**, permita leitura e escrita quando necessário.
2. Habilite **Allow GitHub Actions to create and approve pull requests**.

Os workflows deste projeto usam essa permissão para criar Pull Requests. As
políticas do projeto proíbem o agente de aprovar ou fazer merge automaticamente.

### 5.3 Proteger a branch principal

Configure um ruleset para `main` com, no mínimo:

- Pull Request obrigatório.
- Uma aprovação humana obrigatória.
- Invalidação de aprovação quando houver novo commit.
- Resolução das conversas antes do merge.
- Bloqueio de force push e exclusão da branch.
- Checks obrigatórios após a primeira execução estável.
- Revisão de CODEOWNER para `.github/`, `agente_governanca/` e
  `governanca/politicas/`, quando o recurso estiver disponível.

O usuário ou token dos agentes não deve ter permissão de bypass.

## 6. Estrutura principal

| Caminho | Conteúdo |
| --- | --- |
| `agente/` | Execução das análises de licitações |
| `agente_governanca/` | AI Engineering Governor |
| `casos/` | Documentos e relatórios de cada processo |
| `normas/` | Corpus normativo oficial em PDF |
| `prompts/` | Prompts especializados e índice de gatilhos |
| `governanca/politicas/` | Regras versionadas do governador |
| `governanca/evidencias/` | Evidências geradas em execuções confiáveis |
| `governanca/decisoes/` | Registros de decisões arquiteturais |
| `governanca/riscos/` | Registro e acompanhamento de riscos |
| `.github/workflows/` | Automações do GitHub Actions |
| `roadmap-project.md` | Melhorias priorizadas e critérios de aceite |

## 7. Como os workflows funcionam

### 7.1 `AI Governor - Commit Guard`

Arquivo: `.github/workflows/ai-governor-commit.yml`

É executado em todo push, exceto branches automáticas do governador. Ele:

- usa permissões somente de leitura;
- não recebe chaves dos provedores;
- executa verificações determinísticas;
- executa os testes do governador;
- publica o resumo no GitHub Actions.

Esse workflow deve funcionar mesmo quando nenhuma API de IA estiver disponível.

### 7.2 `AI Engineering Governor`

Arquivo: `.github/workflows/ai-governor.yml`

É executado em Pull Requests, pushes em `main`, manualmente e toda segunda-feira
às 08:17 UTC.

Em Pull Requests, o workflow executa o governador vindo da base confiável e trata
o conteúdo proposto apenas como dados. O código da Pull Request não é executado
com secrets.

Em `main`, o workflow pode gerar evidências e patches em uma branch
`ai-governor/*`, seguida de Pull Request para revisão humana.

O quórum padrão é de dois provedores únicos entre Claude, OpenAI e Gemini. Se o
quórum não for atingido:

- a execução fica `degraded`;
- nenhum patch é aplicado;
- o check falha;
- a causa deve aparecer na evidência.

### 7.3 `Análise automatizada de licitação`

Arquivo: `.github/workflows/analise.yml`

É executado quando arquivos em `casos/**` chegam a `main` ou quando disparado
manualmente. Ele identifica os prompts aplicáveis, chama Claude, grava os
relatórios e abre uma Pull Request `licitacoes-agent/*`.

## 8. Roteiro de avaliação recomendado

### Cenário A: guard determinístico em um commit

Objetivo: confirmar que todo commit é avaliado sem usar IA externa.

1. Crie uma branch de avaliação.
2. Faça uma alteração pequena em um arquivo Markdown.
3. Crie o commit e envie a branch ao GitHub.
4. Abra a aba **Actions**.
5. Localize `AI Governor - Commit Guard`.

Resultado esperado:

- job `deterministic-guard` aprovado;
- testes aprovados;
- resumo com risco e decisão;
- nenhum consumo de API de IA.

### Cenário B: revisão semântica de Pull Request

Objetivo: confirmar separação de privilégios, painel e quórum.

1. Abra uma Pull Request da branch de avaliação para `main`.
2. Aguarde `AI Engineering Governor`.
3. Leia o comentário de evidência publicado na Pull Request.
4. Compare achados, modelos executados, falhas e risco consolidado.

Resultado esperado:

- o checkout confiável vem de `main`;
- o código da proposta é analisado como dados;
- pelo menos dois provedores concluem;
- o maior risco entre os provedores é preservado;
- nenhuma alteração é aplicada à Pull Request analisada.

### Cenário C: falha controlada de provedor

Objetivo: confirmar que indisponibilidade não vira sucesso silencioso.

1. Use temporariamente um ambiente de teste sem um dos três secrets.
2. Execute novamente o workflow do governador.
3. Não remova secrets de produção sem autorização e plano de restauração.

Resultado esperado:

- o provedor ausente aparece como `missing_credentials`;
- dois provedores válidos ainda podem atingir o quórum;
- abaixo de dois, a execução fica `degraded` e não aplica patches.

### Cenário D: Continuous Knowledge Pull

Objetivo: avaliar o processo de atualização das políticas.

1. Acesse `Actions > AI Engineering Governor > Run workflow`.
2. Selecione `main`.
3. Marque `knowledge_pull` como verdadeiro.
4. Execute e acompanhe o job `govern-trusted-ref`.

Resultado esperado:

- consultas limitadas às fontes de `governanca/politicas/FONTES_AUTORIZADAS.md`;
- recomendação com regra atual, mudança externa, impacto e URL direta;
- alteração proposta em branch própria;
- Pull Request aguardando aprovação humana;
- nenhuma política passa a valer automaticamente.

O Gemini participa da análise do repositório, mas atualizações externas e patches
dele são descartados nesse processo enquanto sua busca não oferecer restrição
técnica equivalente por domínio.

### Cenário E: análise de uma licitação sintética

Objetivo: avaliar o agente de domínio sem expor dados reais.

1. Confirme que `ANTHROPIC_API_KEY` está cadastrado.
2. Adicione PDFs oficiais ao diretório `normas/` conforme `normas/README.md`.
3. Copie a estrutura de `casos/EXEMPLO-001/` para um novo caso sintético.
4. Preencha `caso.json` somente com dados fictícios.
5. Adicione um PDF sintético com nome compatível com os padrões de
   `prompts/index.json`, por exemplo um ETP.
6. Abra Pull Request e revise os documentos antes do merge.
7. Após o merge em `main`, acompanhe `Análise automatizada de licitação`.

Resultado esperado:

- prompts aplicáveis identificados pelo nome do arquivo;
- relatórios em `casos/{id}/analises/*.md`;
- atualização de `normas/manifest.json`, quando necessária;
- Pull Request `licitacoes-agent/*` com os relatórios;
- citações e ressalvas revisadas por uma pessoa qualificada.

### Cenário F: execução manual de um prompt

1. Acesse `Actions > Análise automatizada de licitação > Run workflow`.
2. Informe o diretório do caso em `caso`.
3. Informe o identificador existente em `prompts/index.json` no campo `prompt`.
4. Use `documento` somente quando o prompt exigir um arquivo específico.
5. Execute e revise a Pull Request gerada.

Prompts não automatizáveis, como o podcast educativo, permanecem em fluxo manual
fora da API.

## 9. Execução local

### 9.1 Criar o ambiente

Linux, macOS ou WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-governance.txt
```

PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-governance.txt
```

### 9.2 Configurar chaves locais

Crie `.env` a partir de `.env.example`. O arquivo `.env` já está no `.gitignore`,
mas a aplicação não o carrega automaticamente.

Linux, macOS ou WSL:

```bash
set -a
source .env
set +a
```

PowerShell:

```powershell
$env:ANTHROPIC_API_KEY = "valor-local"
$env:OPENAI_API_KEY = "valor-local"
$env:GEMINI_API_KEY = "valor-local"
```

Nunca use valores reais em `.env.example`.

### 9.3 Testar o governador

```bash
python -m unittest discover -s tests -v
python -m agente_governanca --mode deterministic --output resultado-deterministico.md
python -m agente_governanca \
  --providers anthropic,openai,gemini \
  --min-providers 2 \
  --require-ai \
  --omit-patch-content \
  --output resultado-governanca.md
```

Para uma avaliação local, não use `--apply-proposals` até que o time tenha lido
as políticas e compreendido o controle de patches.

### 9.4 Testar o agente de licitações

O agente de licitações usa `requirements.txt` e `ANTHROPIC_API_KEY`:

```bash
python -m pip install -r requirements.txt
python -m agente.executar --caso EXEMPLO-001 --prompt revisao-etp
```

O exemplo precisa conter documentos compatíveis para produzir análise útil. Use
somente material sintético ou autorizado.

## 10. Como ler a evidência do governador

Verifique, nesta ordem:

1. **Status:** `complete`, `degraded` ou `deterministic`.
2. **Risco geral:** maior severidade encontrada.
3. **Decisão recomendada:** `pass`, `pass_with_recommendations` ou
   `changes_required`.
4. **Painel de modelos:** provedores concluídos, modelos, tokens e falhas.
5. **Achados:** evidência concreta, impacto, recomendação e arquivos afetados.
6. **ADRs propostas:** decisões arquiteturais ainda sujeitas à aprovação.
7. **Knowledge Pull:** fontes, regra atual e mudança recomendada.
8. **Patches:** caminhos afetados, rejeições e controles aplicados.

Um relatório `pass` não autoriza merge. O aprovador humano deve conferir o diff,
os checks e o contexto do projeto.

## 11. Diagnóstico de problemas

### `missing_credentials`

Confirme o nome exato do secret e se ele foi criado no repositório correto.
Secrets não são enviados a workflows de forks e contextos não confiáveis.

### `429 insufficient_quota`

A chave chegou ao provedor, mas a conta ou projeto não possui cota disponível.
Confira faturamento, orçamento, limites do projeto e organização da API.

### Quórum `0/2` ou `1/2`

Leia `provider_runs` na evidência. Corrija credencial, cota, modelo ou
indisponibilidade. Não reduza o quórum apenas para deixar o check verde.

### O bot não cria Pull Request

Confirme:

- permissões de escrita do workflow;
- opção de criação de Pull Requests pelo Actions;
- rulesets sem bloqueio indevido ao bot;
- autenticação e mensagens do passo `gh pr create`.

### Nenhum prompt foi aplicado ao documento

Compare o nome e o caminho do arquivo com `entrada_glob` em
`prompts/index.json`. Confirme também `auto_trigger: true`.

### A revisão da PR usa comportamento antigo

O evento `pull_request_target` executa o governador vindo da branch base
confiável. Uma Pull Request que altera o próprio governador será avaliada pela
versão atualmente presente em `main`. Isso é esperado e impede que código não
aprovado obtenha secrets.

### O check determinístico passou, mas o semântico falhou

São controles diferentes. O primeiro valida regras locais sem IA. O segundo
depende de credenciais, cota, rede, SDKs e quórum dos provedores.

## 12. Checklist para liberação ao time

### Configuração

- [ ] Repositório privado.
- [ ] Secrets dos três provedores cadastrados.
- [ ] Cota e faturamento das APIs confirmados.
- [ ] GitHub Actions autorizado a criar Pull Requests.
- [ ] `main` protegida sem bypass do agente.
- [ ] Aprovadores humanos definidos.

### Segurança e dados

- [ ] Primeiros testes usam somente dados sintéticos.
- [ ] Classificação e retenção dos dados foram discutidas.
- [ ] Termos dos provedores foram avaliados.
- [ ] Nenhuma chave aparece em arquivos ou logs.
- [ ] Escopo e acesso ao repositório foram revisados.

### Funcionamento

- [ ] Commit Guard passou.
- [ ] Revisão de Pull Request atingiu quórum `2/3`.
- [ ] Falha de um provedor ficou visível.
- [ ] Nenhum patch foi aplicado sem Pull Request.
- [ ] Continuous Knowledge Pull citou somente fontes autorizadas.
- [ ] Caso sintético gerou relatório revisável.

### Avaliação humana

- [ ] Achados possuem evidência e arquivos afetados.
- [ ] Citações jurídicas foram conferidas na fonte.
- [ ] Custos e tokens foram registrados.
- [ ] Falsos positivos e falsos negativos foram anotados.
- [ ] Riscos, exceções e decisões foram registrados no repositório.

## 13. Limitações atuais

- O agente de licitações ainda usa somente Claude. O painel multi-modelo pertence
  ao governador de engenharia.
- A qualidade jurídica ainda precisa de benchmark com casos sintéticos e
  critérios aprovados.
- O corpus de `normas/` precisa ser populado e validado com fontes oficiais.
- O Gemini não propõe atualização externa durante o Knowledge Pull enquanto não
  houver restrição de busca por domínio equivalente.
- O prompt de podcast educativo depende de fluxo manual no NotebookLM.
- Os controles de CodeQL, dependency review, lock com hashes e observabilidade
  de custos estão priorizados em `roadmap-project.md`.

## 14. Registro da avaliação

Ao final do piloto, registre em uma issue ou documento versionado:

- data e participantes;
- commits e Pull Requests avaliados;
- cenários executados;
- modelos e versões observados;
- custos aproximados;
- achados corretos, falsos positivos e riscos não detectados;
- decisão de continuar, ajustar, restringir ou interromper o uso;
- responsáveis e prazos para cada ação.

O resultado do piloto deve ser uma decisão humana documentada, não apenas um
relatório produzido pelos modelos.
