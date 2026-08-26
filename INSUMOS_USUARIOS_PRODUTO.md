# Insumos Necessários dos Usuários do Produto

## 1. Objetivo

Este documento orienta entrevistas e coleta de material com analistas,
especialistas de negócio, segurança, dados e infraestrutura. O motor só pode ser
homologado depois que as regras abaixo forem fornecidas, revisadas e aprovadas
por pessoas responsáveis.

## 2. Onde cada elemento fica

| Elemento | Local no projeto | Quem fornece ou aprova |
| --- | --- | --- |
| Regras de negócio estruturadas | `conhecimento/regras/*.json` | Especialista de licitações e dono do processo |
| Template de resposta da IA | `conhecimento/templates/*.md` | Dono do produto e analistas |
| Instruções gerais e classificação | `conhecimento/instructions/*.md` | Especialista de negócio, jurídico e risco |
| Skills de análise | `conhecimento/skills/*.md` | Especialista de negócio e equipe de IA |
| Exemplos aprovados e anonimizados | `conhecimento/examples/` | Especialistas e responsável pelos dados |
| Schema da massa de avaliação | `evals/schema-caso-teste.json` | Equipe de qualidade e especialistas |
| Manifestos de teste | Armazenamento controlado, no formato de `evals/` | Equipe de qualidade |
| Atestado real | Upload na API; não fica no Git | Usuário autorizado |
| Requisito da licitação | Campo `requisito` de cada chamada da API | Analista responsável pelo caso |
| PDFs reais da massa | Armazenamento controlado, referenciado por hash | Responsável pelos dados |
| Políticas de IA e dados | `governanca/politicas/` | Segurança, privacidade, jurídico e produto |
| Credenciais das APIs de IA | Secret Manager ou GitHub Actions Secrets | Administrador da plataforma |

O conjunto piloto atualmente disponível é
`conhecimento/regras/atestados-sistemas-operacionais-v1.json`. Ele é apenas um
exemplo e não representa regra homologada para uso material.

## 3. Pacote obrigatório a solicitar aos usuários

### 3.1 Escopo e decisão

Solicitar:

- processo e etapa em que a análise será usada;
- decisão que o resultado apoia e quem continua responsável por ela;
- tipos de requisito e atestado incluídos e explicitamente excluídos;
- estados de saída esperados e quando exigir revisão humana;
- destino da proposta ou rascunho exportado e protocolo de confirmação;
- volume diário, picos simultâneos e prazo esperado para resposta.

### 3.2 Regras de negócio

Para cada critério, coletar:

- identificador, descrição e objetivo;
- se é obrigatório, opcional ou condicional;
- relações `AND`, `OR`, dependência e precedência entre critérios;
- termos aceitos, sinônimos e equivalências autorizadas;
- termos parecidos, mas insuficientes;
- quantidades, unidades, percentuais, períodos e tolerâncias;
- exceções, impedimentos e casos de fronteira;
- evidência mínima necessária no atestado;
- fonte oficial, vigência, proprietário e aprovador da regra;
- exemplos positivos, negativos, parciais e ambíguos.

Não converter entrevista diretamente em regra vigente. O especialista deve
revisar o JSON gerado, os casos de fronteira e o resultado do benchmark.

### 3.3 Atestados, requisitos e gabaritos

Solicitar o pacote inicial descrito em `MASSA_TESTES_PRODUTO.md`, contendo:

- texto exato do requisito associado a cada atestado;
- PDF digital, scan, documento longo e casos inválidos representativos;
- classificação esperada por critério e no resultado consolidado;
- página e trecho que comprovam cada conclusão positiva;
- justificativa para conclusões parciais, negativas ou ambíguas;
- rótulo produzido por dois analistas independentes e eventual desempate;
- autorização de uso, classificação dos dados e hash do documento;
- versão da regra usada para produzir o gabarito.

Atestados reais não devem ser enviados por e-mail, issue, Pull Request ou commit.
Devem entrar por canal controlado e ser removidos da infraestrutura do produto
conforme a política de 10 dias.

### 3.4 Template e forma da resposta

Confirmar com os usuários:

- campos obrigatórios do parecer;
- formato do documento ou integração de destino;
- linguagem, nível de detalhe e terminologia institucional;
- necessidade de página, trecho, justificativa e confiança;
- campos que não podem ser gerados ou exportados;
- regras de arredondamento, ordenação e agrupamento;
- texto de ressalva sobre recomendação da IA e decisão humana;
- identidade e justificativa exigidas na revisão humana.

O template Markdown orienta a tarefa, mas o contrato técnico da resposta é o
JSON Schema definido pelos modelos em `motor_atestados/modelos.py`.

### 3.5 Instruções e fluxo humano

Solicitar:

- como o analista decide hoje, passo a passo;
- fontes consultadas e ordem de prioridade;
- quando deve abster-se e encaminhar para especialista;
- conflitos conhecidos entre regras e como são resolvidos;
- papéis de operador, revisor, aprovador e administrador;
- segregação necessária entre organizações, unidades e casos;
- prazo de revisão e tratamento de divergências entre IA e humano;
- processo para alterar regra, registrar exceção e revogar versão.

### 3.6 Dados, retenção e segurança

Solicitar e aprovar:

- classificação dos documentos e dados pessoais ou sigilosos presentes;
- finalidade, base aplicável, proprietário e usuários autorizados;
- destino externo do resultado e responsável por sua guarda;
- prazo dos metadados mínimos de auditoria;
- hipóteses de guarda legal e quem pode aprová-las;
- região, residência, treinamento e termos aceitos dos provedores;
- requisitos de criptografia, backup, incidente e trilha de acesso.

O prazo de conteúdo na infraestrutura do produto já está definido em
`governanca/politicas/RETENCAO_DADOS.md`: no máximo 10 dias após a conclusão. A
retenção do provedor externo segue os termos contratualmente aceitos.

### 3.7 APIs e modelos de IA

Para cada ambiente e provedor, solicitar:

- provedor e modelo autorizados, com versão fixada quando possível;
- projeto/conta de faturamento e centro de custo;
- chave em Secret Manager, nunca no formulário ou no Git;
- região ou endpoint autorizado;
- limites de requisições e tokens por minuto;
- budget mensal, alertas e responsável por custo;
- timeout, disponibilidade esperada e estratégia de indisponibilidade;
- aceite dos termos de retenção e uso de dados do provedor;
- modelos proibidos e procedimento de troca/homologação.

Assinaturas das interfaces ChatGPT, Claude e Gemini não substituem acesso pago e
credenciais das APIs correspondentes.

## 4. Critério de prontidão

O onboarding de um domínio está pronto somente quando:

- regras possuem fonte, vigência, proprietário, aprovador e versão;
- template, instructions e skills foram aprovados;
- massa de desenvolvimento, regressão e aceitação cega foi separada;
- dois especialistas produziram gabaritos e divergências foram adjudicadas;
- provedores, modelos, budget e limites foram homologados;
- acesso, destino de exportação e retenção foram aprovados;
- falso aceite, citação inventada e vazamento permanecem critérios eliminatórios;
- uma pessoa autorizada registrou o aceite final do piloto.

## 5. Formato recomendado para a coleta

Registrar cada rodada de descoberta em documento versionado contendo:

```text
Domínio/processo:
Proprietário de negócio:
Especialistas participantes:
Decisão apoiada:
Requisitos cobertos:
Critérios e exceções:
Documentos e gabaritos entregues:
Template de saída aprovado:
Fluxo de revisão humana:
Classificação e acessos:
Destino da exportação:
Prazo dos metadados de auditoria:
Provedores/modelos autorizados:
Volume, concorrência e SLO:
Riscos e pendências:
Aprovadores e data:
```
