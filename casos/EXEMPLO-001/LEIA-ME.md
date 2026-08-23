# Como testar com um caso real

1. Renomeie esta pasta para o número real do processo.
2. Ajuste `caso.json` — os campos preenchem os placeholders `{{OBJETO}}`,
   `{{TEMA}}`, `{{EDITAL_TEMA}}` e `{{DOCUMENTO}}` dentro dos prompts.
3. Adicione os documentos do processo usando estes nomes (o agente casa por
   convenção de nome/pasta — ver `entrada_glob` em `prompts/index.json`):
   - `etp.pdf` → dispara revisão de ETP + matriz de riscos
   - `tr.pdf` (ou `termo-referencia.pdf`) → validação de especificações + matriz de riscos + roteiro de fiscalização
   - `edital.pdf` → checklist do edital + advogado do diabo
   - `minuta-contratual.pdf` (ou `contrato.pdf`) → roteiro de fiscalização
   - `cotacoes/*.pdf` → análise comparativa de preços
   - `jurisprudencia/*.pdf` ou `pareceres/*.pdf` → síntese de jurisprudência
   - `propostas-tecnicas/*.pdf` → comparação de propostas
   - `esclarecimentos/*.pdf` ou `impugnacoes/*.pdf` → compilação de FAQ
   - `normas-internas/*.pdf` → só via execução manual (workflow_dispatch)
4. Faça commit e push (ou abra uma PR) — o workflow detecta os arquivos
   novos/alterados e roda os prompts aplicáveis automaticamente.
5. Os relatórios aparecem em `analises/{prompt-id}.md` dentro desta pasta.

Para os prompts sem gatilho automático (contradições normativas, linguagem
simples), dispare manualmente pela aba **Actions → Analise automatizada de
licitacao → Run workflow**, informando `caso`, `prompt` e, se necessário,
`documento`.
