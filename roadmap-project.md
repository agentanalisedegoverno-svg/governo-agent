# roadmap-project

## Objetivo

Evoluir o projeto para uma plataforma auditavel de analise de contratacoes
publicas, com governanca Human-in-the-Loop, seguranca por padrao e independencia
entre provedores de IA.

## Evidencia da analise atual

- Base analisada: commit `71429d5`, branch `feat/multi-model-governor-roadmap`.
- O governador deterministico analisou 44 arquivos textuais permitidos e concluiu
  com risco geral `none`.
- A suite do governador possui 12 testes aprovados e a compilacao Python passou.
- A chamada real ao OpenAI chegou ao provedor, mas retornou `429
  insufficient_quota`; portanto, nao houve parecer semantico OpenAI nesta rodada.
- Claude e Gemini nao possuem credenciais locais para compor o quorum nesta
  execucao. A ativacao em GitHub Actions exige os tres repository secrets.

Ausencia de achado deterministico nao equivale a ausencia de risco. As prioridades
abaixo combinam os controles automatizados com revisao direta do codigo,
workflows, politicas e estrutura documental.

## P0 - Ativar a governanca multi-modelo

### GOV-001 - Credenciais, cota e quorum

Configurar `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` e `GEMINI_API_KEY` nos GitHub
Actions Secrets. Habilitar faturamento/cota no projeto OpenAI e validar que ao
menos dois provedores independentes concluem cada avaliacao.

**Criterio de aceite:** execucao manual do workflow com quorum `2/3`, relatorio
com modelo, uso de tokens e falhas por provedor, sem exposicao das chaves.

### GOV-002 - Protecao da branch e permissao de PR

Habilitar a criacao de Pull Requests pelo GitHub Actions e proteger `main` com
PR obrigatoria, aprovacao humana, invalidacao de aprovacao apos novo commit,
conversas resolvidas e revisao de CODEOWNER para codigo e politicas do agente.

**Criterio de aceite:** o bot cria a branch e a PR, mas nao consegue aprovar,
fazer merge ou contornar o ruleset.

### GOV-003 - Evidencia mesmo em modo degradado

Manter a criacao da PR de evidencia quando o quorum falhar. A execucao deve
continuar marcada como falha, com causa objetiva e sem aplicar patches.

**Criterio de aceite:** uma chave ausente ou provedor indisponivel gera evidencia
`degraded`, nenhum patch e check vermelho visivel na PR.

## P1 - Seguranca e confiabilidade

### SEC-001 - Isolamento dos documentos de caso

Validar e resolver `caso`, `documento` e todos os caminhos recebidos pelo
workflow antes de ler arquivos. Bloquear caminhos absolutos, `..`, links
simbolicos e qualquer arquivo fora de `casos/{id}`. Definir limite de tamanho,
quantidade e tipos MIME aceitos antes do envio a provedores.

**Criterio de aceite:** testes cobrem path traversal, symlink escape, arquivo
grande e tipo nao permitido; nenhum caso consegue acessar dados de outro caso.

### SEC-002 - Pipeline especializado de seguranca

Adicionar CodeQL, dependency review, secret scanning e atualizacao automatizada
de dependencias. Fixar dependencias transitivas com lock e hashes, mantendo os
GitHub Actions referenciados por SHA.

**Criterio de aceite:** PRs exibem checks separados para SAST, secrets e
dependencias vulneraveis; achados altos ou criticos bloqueiam merge.

### REL-001 - Resiliencia dos provedores

Definir timeout, retry com backoff e jitter, circuit breaker e classificacao
estavel de erros para cada API. Nao repetir erros de autenticacao ou cota. O
quorum deve contar provedores unicos, nunca duas chamadas ao mesmo fornecedor.

**Criterio de aceite:** testes simulam timeout, 429, 5xx, resposta JSON invalida e
falha parcial sem perder os resultados dos demais modelos.

### REL-002 - Testes dos adaptadores e contratos

Criar testes unitarios com clientes falsos para os parametros oficiais de Claude,
OpenAI Responses API e Gemini Interactions API. Adicionar um smoke test manual,
sem dados de casos, para detectar modelos removidos ou mudancas de SDK.

**Criterio de aceite:** nenhuma mudanca de adaptador entra sem teste de contrato;
o smoke test registra somente metadados e pode ser executado sob demanda.

## P2 - Qualidade do produto de licitacoes

### DATA-001 - Corpus normativo verificavel

Popular `normas/` apenas com PDFs oficiais, registrando URL de origem, orgao,
versao, data de vigencia, checksum e data da coleta. Criar rotina de revisao para
norma revogada, substituida ou alterada.

**Criterio de aceite:** cada conclusao juridica pode ser rastreada ate pagina,
arquivo, checksum e fonte oficial vigente.

### AI-001 - Avaliacao de prompts e modelos

Criar conjunto de casos sinteticos e anonimizados com criterios esperados para
citacao, cobertura, contradicao, abstencao e linguagem. Medir qualidade antes de
trocar prompt, modelo ou provedor.

**Criterio de aceite:** regressao possui baseline versionada, limiares por tipo de
analise e aprovacao humana para mudancas que reduzam qualidade ou seguranca.

### AI-002 - Independencia no agente de dominio

O governador de engenharia ja usa Claude, GPT/OpenAI e Gemini, mas o agente que
produz analises de licitacao ainda depende da API Claude. Antes de ampliar esse
fluxo, definir estrategia por risco: consenso para conclusoes criticas, modelo
secundario para verificacao e fallback apenas quando o benchmark demonstrar
equivalencia.

**Criterio de aceite:** ADR aprovada, esquema de saida comum, citacoes preservadas
e benchmark comparativo sem reducao silenciosa da qualidade juridica.

### PROD-001 - Validacao dos casos

Definir JSON Schema para `caso.json`, estados da analise, idempotencia e
versionamento dos relatorios. Separar claramente erro operacional, informacao
ausente, ressalva juridica e conclusao do modelo.

**Criterio de aceite:** entrada invalida falha antes de consumir tokens e cada
relatorio identifica entradas, prompt, modelo e versoes utilizadas.

## P3 - Privacidade, dados e operacao

### PRIV-001 - Ciclo de vida dos dados

Aplicar a politica versionada em `governanca/politicas/RETENCAO_DADOS.md`:
classificar dados, registrar conclusao e exportacao, calcular expiracao, remover
conteudo em ate 10 dias e tratar incidentes. Documentar e aceitar os termos de
cada provedor quanto a treinamento, retencao, residencia e subprocessadores;
Zero Data Retention nao e requisito deste produto.

**Criterio de aceite:** matriz de dados aprovada; `completed_at` e `expires_at`;
job idempotente com alertas D+7/D+9 e expurgo D+10; exclusao comprovada em
objetos, banco, indices, caches, temporarios e backups; apenas metadados minimos
permanecem; evidencia de que somente o necessario e enviado a cada API.

### OBS-001 - Observabilidade e custos

Registrar por execucao provedor, modelo, latencia, tokens, cache, custo estimado,
tentativas, resultado do quorum e motivo de falha. Definir budget, alertas e SLO
sem registrar documentos, prompts sensiveis ou respostas integrais em logs.

**Criterio de aceite:** dashboard ou relatorio mensal demonstra disponibilidade,
custo por caso, taxa de quorum e principais causas de degradacao.

### OPS-001 - Controle de ruido e duplicidade

Evitar uma nova PR de evidencia para o mesmo commit e consolidar execucoes
repetidas. Definir expiracao e limpeza de branches do bot e politica de retencao
dos artefatos de governanca.

**Criterio de aceite:** uma unidade de avaliacao possui uma PR ativa, atualizada
de forma idempotente, com branch removida depois do merge ou encerramento.

## P4 - Continuous Knowledge Pull

### KNO-001 - Coleta verificavel

Claude e OpenAI podem executar busca com allowlist aplicada na propria API. O
Gemini deve continuar excluido de propostas de atualizacao externa enquanto a
sua busca nao oferecer restricao equivalente por dominio. Filtragem posterior
isolada nao e controle suficiente.

**Criterio de aceite:** cada recomendacao externa registra URL direta, data de
consulta, regra atual, mudanca detectada, impacto, arquivo recomendado e estado
de aprovacao humana.

### KNO-002 - Memoria operacional versionada

Padronizar ADRs, riscos, excecoes e decisoes humanas com identificador,
proprietario, status, evidencia, risco residual e prazo de revisao. Nenhuma
mudanca externa altera automaticamente as politicas vigentes.

**Criterio de aceite:** toda alteracao de politica possui PR, diff revisavel,
fonte autorizada e decisao humana registrada e reversivel.

## Ordem recomendada

1. Consolidar o Knowledge Repository do MVP com taxonomia, metadata e autoridade.
2. Resolver `GOV-001` e `GOV-002` para tornar o ciclo executavel.
3. Entregar `SEC-001`, `REL-001` e `REL-002` antes de enviar casos reais.
4. Construir `DATA-001`, `AI-001` e `PROD-001` para validar qualidade juridica.
5. Aprovar `PRIV-001` antes de ampliar usuarios, orgaos ou volume de documentos.
6. Evoluir observabilidade, idempotencia e Knowledge Pull com evidencias mensuraveis.

## Arquitetura de evolucao

O caminho aprovado para o MVP esta em `ARQUITETURA.md`. A decisao central e
evitar banco, vector store e servidor permanente na V1, usando GitHub privado,
Markdown, JSON, busca textual e revisao humana. PostgreSQL, pgvector, MCP Server,
fila, object storage, OCR e RBAC entram somente quando a massa homologada e o
volume justificarem a complexidade.

### KREP-001 - Taxonomia do Knowledge Repository

Criar a estrutura expandida de `conhecimento/` para `products/`, `vendors/`,
`checklists/` e `schemas/`, mantendo compatibilidade com o motor atual.

**Criterio de aceite:** README do conhecimento documenta a taxonomia; novos
artefatos possuem local definido; nada exige RAG ou banco para funcionar.

### KREP-002 - Metadata e hierarquia de autoridade

Padronizar front matter de Markdown com `id`, `type`, `domain`, `status`,
`version`, `owner`, `authority` e `classification`. Definir a precedencia
`policy > rule > standard > template > knowledge > example`.

**Criterio de aceite:** exemplos documentados; checklist de revisao inclui status
e autoridade; a IA e instruida a preferir `status: approved` em uso material.

## Indicadores de acompanhamento

- Percentual de commits e PRs avaliados pelo governador.
- Taxa de quorum completo e de execucoes degradadas.
- Tempo medio ate decisao humana e idade de riscos abertos.
- Vulnerabilidades por severidade e tempo de correcao.
- Custo e latencia por caso, prompt, modelo e provedor.
- Taxa de citacoes verificaveis e de abstencao correta nos benchmarks.
- Excecoes vencidas, politicas sem revisao e fontes externas desatualizadas.
