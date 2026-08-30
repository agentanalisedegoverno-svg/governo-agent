# Checklist Operacional do Projeto

Snapshot: 2026-08-30

Este arquivo registra o estado pratico do projeto em tres grupos: `Done`,
`Doing` e `To do`. O roadmap tecnico continua em `roadmap-project.md`; este
checklist serve para acompanhamento rapido de execucao, dependencias externas e
proximas acoes.

## Done

- Documentacao principal consolidada no `README.md`, com arquitetura, execucao
  local, seguranca, limitacoes e operacao do piloto.
- Decisao de MVP registrada em `ARQUITETURA.md`: GitHub privado como fonte de
  verdade, Markdown/YAML/JSON versionados e RAG somente em fase posterior.
- Plano de piloto para aproximadamente 10 usuarios registrado em
  `PLANO_PILOTO_10_USUARIOS.md`.
- Knowledge Repository inicial criado em `conhecimento/`, com taxonomia para
  produtos, fornecedores, checklists, schemas, regras, templates, instructions e
  skills.
- Metadata de artefatos Markdown padronizada e validada por testes.
- Schema inicial de `caso.json` registrado em `schemas/caso.schema.json`.
- Validacoes de seguranca do agente documental implementadas para caso,
  documento, caminhos, tipo de arquivo, tamanho e limite de documentos.
- Motor de Validacao de Atestados mantido como PoC executavel `0.1`, com API,
  verificacao literal de evidencias, trilha append-only e revisao humana.
- GitHub Actions habilitado com permissao de leitura/escrita para workflows e
  criacao de Pull Requests pelo Actions.
- Secrets `GEMINI_API_KEY` e `OPENAI_API_KEY` adicionados ao repositorio.
- Falha de credito OpenAI evidenciada no workflow `33334021966`: retorno
  `429 insufficient_quota` / `credit_balance_exhausted`.
- Bug do cliente Gemini corrigido em `agente_governanca/provedores.py` e
  `motor_atestados/provedores.py`.
- Pull Request `#20 fix: manter cliente Gemini ativo` mesclado em `main` em
  2026-08-30.
- Workflow manual do AI Governor preparado para teste temporario somente com
  Gemini: `providers=gemini`, `min_providers=1`.
- Execucao remota somente com Gemini validada com sucesso no run
  `33334775581`.
- Pull Request de evidencia do run Gemini-only criado pelo Governor:
  `#21 governance: avaliacao do commit ef445c69b479`.
- Dependabot PRs `#15` e `#14` mesclados em `main`.
- Timeout configuravel dos provedores do Governor implementado na branch
  `fix/governor-provider-timeout`, com `AI_GOVERNOR_PROVIDER_TIMEOUT_SECONDS`
  e padrao de 180 segundos.
- Suite automatizada local validada com 44 testes aprovados.
- Execucao manual da branch `fix/governor-provider-timeout` com Gemini-only
  concluida com sucesso no run `33335848855`.

## Doing

- Pull Request `#24 fix: limitar timeout dos provedores do Governor` aberto
  para levar o timeout de provedores para `main`.
- Pull Request de evidencia `#25 governance: avaliacao do commit 494b48ec9086`
  aberto a partir do run manual Gemini-only da branch `#24`.
- Pull Request Dependabot `#12` aberto para atualizar FastAPI.
- Pull Request de evidencia antigo `#18` aberto e com conflito em relacao ao
  estado atual de `main`.
- Validacao temporaria do AI Governor com apenas Gemini enquanto Claude e
  OpenAI nao estao disponiveis para quorum completo.
- Organizacao das Pull Requests de evidencia abertas pelo Governor para reduzir
  ruido operacional.
- Preparacao da primeira homologacao do fluxo com massa sintetica e sem dados
  reais de licitacao.
- Documentacao operacional sendo mantida no repositorio para que as proximas
  decisoes fiquem rastreaveis por commit.

## To do

- Fazer merge do PR `#24` em `main` apos revisao humana.
- Rodar o AI Governor em `main` com `providers=gemini` e `min_providers=1` apos
  o merge do PR `#24`, confirmando que o timeout e o Gemini-only estao ativos
  na branch protegida.
- Revisar se o PR `#25` deve ser mesclado como evidencia ou fechado para evitar
  ruido operacional.
- Revisar o PR `#12` de FastAPI apos checks e conflito/estado de merge.
- Adicionar `ANTHROPIC_API_KEY` quando a conta Claude API estiver pronta.
- Resolver cota/faturamento OpenAI ou manter OpenAI fora dos testes temporarios.
- Retornar ao quorum padrao `2/3` assim que pelo menos dois provedores
  independentes estiverem operacionais.
- Revisar, fechar ou fazer merge das PRs de evidencia antigas, mantendo somente
  evidencias uteis e atuais.
- Confirmar protecao de `main` com PR obrigatoria, aprovacao humana,
  conversas resolvidas e CODEOWNERS.
- Considerar migracao para GitHub Team se for necessario enforcement real de
  rulesets em repositorio privado.
- Preparar ambiente piloto unico para ate 10 usuarios, com VPN ou rede privada,
  TLS, reverse proxy, limite de upload e `MOTOR_API_KEY`.
- Configurar host do piloto com `GEMINI_API_KEY`, `.motor-data` em volume
  criptografado, logs sanitizados e processo Uvicorn gerenciado.
- Criar massa sintetica de PDFs e casos para homologacao juridica e tecnica.
- Executar smoke test do motor com PDF sintetico antes de qualquer dado real.
- Implementar rotina automatizada de lifecycle e expurgo conforme politica:
  alertas D+7/D+9 e remocao D+10.
- Planejar evolucao para autenticacao individual, RBAC, rate limiting,
  PostgreSQL, object storage, fila, OCR, antimalware/CDR e observabilidade.
- Definir baseline de custo, latencia, tokens, taxa de quorum e qualidade das
  citacoes com a massa de homologacao.

## Pendencias que dependem do usuario

- Informar quando `ANTHROPIC_API_KEY` estiver disponivel.
- Confirmar se a cota/faturamento OpenAI sera ativada agora ou se OpenAI ficara
  desabilitada ate segunda fase.
- Aprovar ou orientar o destino das Pull Requests abertas no GitHub.
- Definir onde o piloto para 10 usuarios sera hospedado e quem tera acesso.
- Fornecer ou autorizar a criacao da massa sintetica de documentos para
  homologacao.
