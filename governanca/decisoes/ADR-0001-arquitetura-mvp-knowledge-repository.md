# ADR-0001 - MVP como Knowledge Repository Governado

## Status

Proposta para aprovacao humana.

## Contexto

O projeto precisa iniciar com baixo custo operacional, rastreabilidade e capacidade
de atender um piloto restrito. A base atual ja possui motor de atestados, agente
documental, prompts, regras versionadas, governanca e testes.

Introduzir banco vetorial, RAG completo, filas, object storage e multiplas
replicas antes da homologacao aumentaria complexidade sem resolver o principal
risco atual: organizacao, qualidade e aprovacao do conhecimento.

## Decisao

Operar a V1 como Knowledge Repository governado para IA:

- GitHub privado como fonte de verdade;
- Markdown para conhecimento explicativo;
- JSON para regras executaveis e schemas;
- busca textual e selecao explicita de contexto;
- Pull Request e aprovacao humana para mudancas;
- motor local ou servidor unico para piloto compartilhado;
- RAG, pgvector e MCP Server apenas em evolucao posterior.

## Consequencias

Beneficios:

- custo de infraestrutura minimo;
- revisao humana simples via Git;
- historico e diffs auditaveis;
- menor superficie operacional no piloto;
- caminho claro para RAG futuro sem reorganizar a base.

Limitacoes:

- recuperacao semantica ainda nao automatizada;
- persistencia local nao suporta multiplas replicas;
- autenticacao individual e RBAC ficam fora da V1;
- documentos reais exigem controles operacionais externos ate a automacao de
  lifecycle ser entregue.

## Criterio de revisao

Revisar esta decisao quando houver massa homologada, volume real de uso,
necessidade de busca semantica ou exigencia de operacao multiusuario com
segregacao forte.

