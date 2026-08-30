# Corpus normativo

Coloque aqui os PDFs oficiais que formam a base fixa de referência para todas
as análises. O nome do arquivo é livre — o agente indexa qualquer `*.pdf`
desta pasta e faz upload (ou reaproveita, via `manifest.json`) automaticamente
na primeira execução após uma mudança.

Normas são fontes de autoridade alta no Knowledge Repository. Cada PDF deve ter
origem oficial, data de coleta, checksum e status de vigência conhecidos antes de
ser usado em análise material. Quando uma norma for extensa, crie também um
resumo técnico em Markdown no conhecimento adequado, apontando página, seção e
arquivo-fonte.

Sugestão de conteúdo, conforme o desenho original do projeto:

- Lei nº 14.133/2021 (Nova Lei de Licitações)
- Decreto nº 11.462/2023 (Sistemas de Dispensa Eletrônica / Registro de Preços)
- IN SEGES/ME nº 65/2021 (Pesquisa de Preços)
- Lei nº 15.263/2025 (Política Nacional de Linguagem Simples)
- Regulamentos e manuais internos do órgão

`manifest.json` é gerado e atualizado automaticamente pelo workflow — não
edite manualmente. Ele guarda o `file_id` da Files API e o checksum de cada
PDF, para não reenviar arquivos que não mudaram.

Não misture minutas, cópias sem origem, documentos revogados ou interpretações
internas nesta pasta sem identificar claramente o status. Interpretações,
checklists e padrões derivados devem ficar em `conhecimento/`, com metadata e
aprovação humana.
