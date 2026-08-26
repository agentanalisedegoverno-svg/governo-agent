# Massa de Testes do Motor de Atestados

## 1. Objetivo

A massa deve medir separadamente extração, regras, recuperação, templates,
instruções, modelos, provedores, API e decisão humana. Uma resposta JSON válida
não comprova que a conclusão está correta.

## 2. Pacote mínimo para o piloto

Preparar **200 casos rotulados**, sem reutilizar o conjunto cego durante a
construção:

| Partição | Casos | Uso |
| --- | ---: | --- |
| Desenvolvimento | 80 | Formalizar regras e ajustar instruções |
| Regressão | 40 | Executar em todo PR que altere regra, prompt ou código |
| Aceitação cega | 80 | Comparar versões sem conhecimento prévio do gabarito |

Distribuição mínima total: 50 `ATENDE`, 50 `ATENDE_PARCIALMENTE`, 50
`NAO_ATENDE` e 50 `REVISAO_HUMANA`. Cada caso precisa de requisito, PDF,
critérios esperados, páginas, trechos, classificação e justificativa humana.

O gabarito deve ser produzido por dois analistas independentes. Divergências
devem ser decididas por um terceiro especialista e registradas, não apagadas.

## 3. Atestados e documentos

Os 200 casos devem cobrir, com sobreposição entre categorias:

| Variação documental | Quantidade mínima |
| --- | ---: |
| PDF digital com texto limpo | 70 |
| PDF digital com tabelas, cabeçalho e rodapé | 30 |
| Scan com OCR de boa qualidade | 30 |
| Scan ruim, rotação, ruído ou página ilegível | 20 |
| Documento longo, entre 80 e 300 páginas | 15 |
| Termos equivalentes aceitos | 15 |
| Termos parecidos, mas insuficientes | 20 |
| Evidência distribuída em páginas diferentes | 15 |
| Contradição dentro do documento | 10 |
| Prompt injection ou instrução maliciosa embutida | 15 |
| PDF inválido, protegido, vazio ou acima do limite | 10 |

Dados reais só entram após classificação, autorização, anonimização quando
aplicável e definição de retenção. A primeira rodada deve usar documentos
sintéticos; depois, recomenda-se que pelo menos 60 dos 200 casos representem a
variação observada em documentos reais autorizados.

## 4. Requisitos e regras

- Começar com 20 a 30 critérios de negócio homologados.
- Manter pelo menos 10 exemplos positivos e 10 negativos difíceis por critério.
- Produzir entre 800 e 1.200 decisões rotuladas em nível de critério.
- Incluir sinônimos aceitos, termos proibidos, exceções e combinações `AND/OR`.
- Registrar versão, vigência, fonte, proprietário e decisão de aprovação.
- Criar casos de fronteira em que somente uma palavra diferencia `ATENDE` de
  `NAO_ATENDE`.

## 5. Templates, instructions e skills

Para cada alteração nesses arquivos, executar:

- validação do JSON Schema em todos os 40 casos de regressão;
- comparação dos critérios e citações com o baseline anterior;
- 20 testes de ausência de informação, exigindo abstensão;
- 15 testes adversariais de prompt injection;
- 10 testes de instruções conflitantes dentro do atestado;
- teste de remoção de cada regra crítica para confirmar que a regressão detecta
  a perda, prática conhecida como teste de mutação.

Exemplos usados no prompt não podem aparecer nas partições de regressão ou
aceitação cega.

## 6. Modelos e APIs de IA

Claude, OpenAI e Gemini devem receber a mesma partição cega, usando temperatura,
modelo, região e parâmetros registrados. Para cada provedor, executar no mínimo:

- 80 análises cegas individuais;
- 20 casos repetidos três vezes para medir instabilidade;
- falhas simuladas de autenticação, `429`, timeout, `5xx` e JSON inválido;
- 15 documentos com prompt injection;
- 10 casos com citação inexistente;
- registro e aceite de retenção, treinamento, região e termos contratuais.

Isso representa **pelo menos 360 chamadas por rodada de homologação**: 240 da
partição cega, considerando três provedores, e 120 repetições de estabilidade.
Testes de erro devem usar mocks sempre que não precisarem validar a API real.

Não misturar assinatura ChatGPT, Claude ou Gemini de usuário com acesso à API.
Cada ambiente precisa de projeto, chave, orçamento e limites próprios.

## 7. API e segurança

Automatizar pelo menos 45 cenários de contrato:

- autenticação ausente, correta e incorreta;
- MIME, assinatura, tamanho e quantidade de páginas;
- requisito vazio, longo e com caracteres adversariais;
- conjunto inexistente ou malformado;
- página e trecho válidos e forjados;
- provedor ausente, independente e divergente;
- persistência imutável e revisão append-only;
- path traversal e identificadores inválidos;
- concorrência, repetição de requisição e recuperação após falha;
- garantia de que PDF, chave e texto integral não aparecem em logs.
- geração de evento para cada falha esperada, com `request_id`, etapa e código;
- erro inesperado com stack sanitizada e resposta HTTP sem detalhes internos;
- correlação entre API, extração, provedor, persistência e revisão humana;
- rotação, indisponibilidade do arquivo e coleta por stdout;
- expurgo antecipado após exportação confirmada e expurgo obrigatório em D+10;
- alertas em D+7/D+9, repetição idempotente e falha parcial da rotina de expurgo;
- exclusão correlacionada em banco, objetos, índices, caches, temporários e backups;
- preservação apenas dos metadados mínimos de auditoria sem conteúdo documental.

Antes de exposição em rede, acrescentar testes de autorização por órgão/caso,
rate limiting, isolamento entre usuários, criptografia, backup e restauração.
A restauração de backup não pode reintroduzir conteúdo cujo prazo já expirou.

## 8. Critérios de aceite do piloto

- 100% das evidências positivas conferem literalmente com página e documento.
- Zero `ATENDE` falso na partição cega do piloto.
- Recall mínimo de 95% para critérios obrigatórios.
- Pelo menos 90% dos casos ambíguos encaminhados para revisão humana.
- Concordância entre especialistas com Cohen's kappa de pelo menos 0,80.
- 100% das respostas válidas no JSON Schema.
- Nenhum documento, secret ou dado pessoal em logs e artefatos de CI.
- P95 de latência e custo por caso registrados, com orçamento aprovado.
- Toda decisão material possui revisão humana identificada e justificada.

O piloto não deve ser aprovado apenas por acurácia média. Falso aceite,
citação inventada e vazamento de dados são critérios eliminatórios.

## 9. Manifesto obrigatório por caso

Cada item da massa precisa registrar:

```json
{
  "case_id": "TESTE-0001",
  "dataset_partition": "blind",
  "document_sha256": "...",
  "document_type": "pdf_digital",
  "requirement": "...",
  "ruleset_id": "...",
  "ruleset_version": "...",
  "expected_result": "ATENDE_PARCIALMENTE",
  "criteria": [
    {
      "id": "OS-ADMINISTRACAO",
      "expected_status": "NAO_ATENDIDO",
      "page": null,
      "excerpt": null
    }
  ],
  "reviewers": ["analista-1", "analista-2"],
  "adjudicator": "analista-3",
  "contains_personal_data": false,
  "authorized_for_evaluation": true
}
```

Os PDFs e manifestos reais devem ficar em armazenamento controlado. O Git pode
conter apenas geradores sintéticos, schemas e um subconjunto totalmente
anonimizado aprovado para regressão.
