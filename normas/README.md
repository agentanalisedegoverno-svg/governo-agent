# Corpus normativo

Coloque aqui os PDFs oficiais que formam a base fixa de referência para todas
as análises. O nome do arquivo é livre — o agente indexa qualquer `*.pdf`
desta pasta e faz upload (ou reaproveita, via `manifest.json`) automaticamente
na primeira execução após uma mudança.

Sugestão de conteúdo, conforme o desenho original do projeto:

- Lei nº 14.133/2021 (Nova Lei de Licitações)
- Decreto nº 11.462/2023 (Sistemas de Dispensa Eletrônica / Registro de Preços)
- IN SEGES/ME nº 65/2021 (Pesquisa de Preços)
- Lei nº 15.263/2025 (Política Nacional de Linguagem Simples)
- Regulamentos e manuais internos do órgão

`manifest.json` é gerado e atualizado automaticamente pelo workflow — não
edite manualmente. Ele guarda o `file_id` da Files API e o checksum de cada
PDF, para não reenviar arquivos que não mudaram.
