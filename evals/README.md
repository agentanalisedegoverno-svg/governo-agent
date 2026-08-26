# Avaliações do produto

Os manifestos de casos devem seguir `schema-caso-teste.json`. O Git recebe apenas
manifestos e documentos totalmente sintéticos ou anonimizados e autorizados.
PDFs reais permanecem em armazenamento controlado e são referenciados por hash.

Partições permitidas:

- `development`: pode orientar a construção das regras;
- `regression`: executada em mudanças de código, regra, template ou modelo;
- `blind`: gabarito oculto durante a execução de homologação.

O benchmark futuro deverá ler esses manifestos, executar cada configuração de
provedor e produzir métricas por resultado, critério, citação, custo e latência.
