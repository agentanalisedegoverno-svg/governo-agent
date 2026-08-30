# Avaliações do produto

Os manifestos de casos devem seguir `schema-caso-teste.json`. O Git recebe apenas
manifestos e documentos totalmente sintéticos ou anonimizados e autorizados.
PDFs reais permanecem em armazenamento controlado e são referenciados por hash.

No MVP, as avaliações também devem medir a qualidade do Knowledge Repository:
metadata preenchida, autoridade correta, status aprovado, referências válidas e
separação entre exemplos de prompt e casos cegos.

Partições permitidas:

- `development`: pode orientar a construção das regras;
- `regression`: executada em mudanças de código, regra, template ou modelo;
- `blind`: gabarito oculto durante a execução de homologação.

O benchmark futuro deverá ler esses manifestos, executar cada configuração de
provedor e produzir métricas por resultado, critério, citação, custo e latência.

Alterações em `conhecimento/`, `prompts/` ou `normas/` devem ser avaliadas contra
a partição de regressão antes de serem usadas em casos reais.

Os testes locais tambem verificam o contrato minimo de `schemas/caso.schema.json`
e a metadata dos Markdown de conhecimento. Isso evita consumir tokens com casos
malformados ou conhecimento sem governanca minima.
