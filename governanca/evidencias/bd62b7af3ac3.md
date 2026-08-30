<!-- ai-engineering-governor -->
# Evidencia do AI Engineering Governor

- Repositorio: `agentanalisedegoverno-svg/governo-agent`
- Commit: `bd62b7af3ac32a9d53c502fed009292b533068d3`
- Branch/ref: `main`
- Evento: `push`
- Execucao: `33336254761`
- Gerado em UTC: `2026-08-30T21:22:56.172812+00:00`
- Status: **degraded**
- Risco geral: **none**
- Decisao recomendada: **pass**

## Resumo executivo

Nenhum provedor de IA concluiu a analise.

## Painel de modelos

- Quorum minimo: `2`
- Provedores concluidos: `0`
- Quorum atingido: `False`

- **anthropic**: falha `missing_credentials` - ANTHROPIC_API_KEY nao configurada.
- **openai**: falha `RateLimitError` - Error code: 429 - {'error': {'message': 'You have no credits remaining. Add credits to continue using the API at https://platform.openai.com/settings/organization/billing/.', 'type': 'insufficient_quota', 'param': None, 'code': 'credit_balance_exhausted'}}
- **gemini**: falha `RateLimitError` - Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-3.7-flash\nPlease retry in 4.853364811s.', 'code': 'too_many_requests'}}

## Riscos e recomendacoes

Nenhum achado foi registrado nesta execucao.

## Decisoes arquiteturais propostas

Nenhuma ADR foi proposta.

## Continuous Knowledge Pull

Nenhuma mudanca externa relevante foi confirmada nesta execucao.

## Alteracoes propostas

Nenhum patch foi proposto.

## Controles de execucao

- Arquivos textuais considerados: `92`
- Patches validados e aplicados na branch de trabalho: `0`
- Patches rejeitados pelos controles: `0`
- Atualizacoes externas rejeitadas por fonte: `0`
- Merge ou aprovacao automatica: `proibido`
- Alteracoes na branch protegida: `proibido`

---
Esta evidencia e uma recomendacao tecnica sujeita a revisao humana. Ela nao autoriza merge, deploy ou alteracao de politica.
