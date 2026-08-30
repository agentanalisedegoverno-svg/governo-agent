# Continuous Knowledge Pull

O processo e executado semanalmente e pode ser disparado manualmente.

Fluxo obrigatorio:

`detectar -> comparar -> avaliar impacto -> registrar evidencia -> recomendar -> propor Markdown -> abrir PR -> aguardar humano`

Uma mudanca externa so justifica proposta quando for relevante para tecnologias
presentes no repositorio ou para seus riscos. A proposta deve apontar a regra
atual, a fonte autorizada, o impacto, a mudanca recomendada e as consequencias.

O agente nao deve editar silenciosamente politicas, ampliar suas fontes, reduzir
controles ou considerar uma recomendacao vigente antes do merge humano.

No MVP, o Knowledge Pull atualiza conhecimento versionado, nao um indice vetorial
em producao. Toda recomendacao deve resultar em Markdown, JSON ou ADR revisavel
por Pull Request. Bancos, embeddings e MCP Server fazem parte da evolucao futura
descrita em `../../ARQUITETURA.md`.
