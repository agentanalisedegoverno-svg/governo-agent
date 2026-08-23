# Matriz de Riscos

## Severidade

- `critical`: exposicao ativa de credencial ou dado sensivel, execucao remota,
  perda irreversivel, bypass de governanca ou comprometimento sistemico.
- `high`: impacto amplo em confidencialidade, integridade, disponibilidade,
  privacidade ou conformidade, com exploracao ou falha plausivel.
- `medium`: degradacao relevante, divida ou controle incompleto com impacto limitado.
- `low`: melhoria localizada sem risco material imediato.
- `info`: observacao ou oportunidade sem risco demonstrado.

## Decisao recomendada

- Qualquer achado `critical` ou `high`: `changes_required`.
- Achados apenas `medium` ou `low`: `pass_with_recommendations`.
- Sem achados materiais: `pass`.

Se a evidencia for insuficiente, o agente deve reduzir a confianca e declarar a
informacao ausente. Ausencia de evidencia nao equivale a ausencia de risco.
