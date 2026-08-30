# Manual do Motor Governado de Validação de Atestados

## 1. Escopo da versão 0.1

Esta versão recebe um requisito e um atestado em PDF, aplica um conjunto de
regras versionado, consulta um provedor de IA e devolve uma recomendação
estruturada com critérios, páginas, trechos e alertas. Toda análise exige revisão
humana antes de produzir uma decisão material.

O motor é o primeiro consumidor executável do Knowledge Repository do projeto.
Ele não implementa RAG vetorial nesta versão: o conjunto de regras selecionado
carrega explicitamente os arquivos de `conhecimento/regras/`,
`conhecimento/templates/`, `conhecimento/instructions/` e
`conhecimento/skills/`.

O PDF é extraído em memória e não é salvo pelo piloto. A trilha contendo hash,
evidências, pareceres e revisões é gravada em `.motor-data/`, diretório ignorado
pelo Git. Para produção, esse repositório local deverá ser substituído por banco
e armazenamento imutável com controle de acesso.

## 2. Preparação

Requisitos:

- Python 3.12;
- uma chave de Claude, OpenAI ou Gemini;
- um segredo local para proteger a API;
- PDF digital com texto extraível e até 20 MB e 300 páginas.

Instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-product.txt
```

Configure somente o provedor que será usado. O exemplo abaixo usa OpenAI:

```powershell
$env:OPENAI_API_KEY = "sua-chave"
$env:ATESTADOS_PROVIDER = "openai"
$env:ATESTADOS_OPENAI_MODEL = "modelo-homologado-pelo-time"
$env:MOTOR_API_KEY = "segredo-local-longo-e-aleatorio"
$env:MOTOR_DATA_DIR = ".motor-data"
```

Para Claude, use `ANTHROPIC_API_KEY` e `ATESTADOS_ANTHROPIC_MODEL`. Para Gemini,
use `GEMINI_API_KEY` e `ATESTADOS_GEMINI_MODEL`. Assinaturas de interfaces como
ChatGPT não substituem crédito e chave da API correspondente.

## 3. Iniciar a API

```powershell
python -m motor_atestados
```

A API escuta somente em `http://127.0.0.1:8000`. A documentação interativa fica
em `http://127.0.0.1:8000/docs`.

Verifique o serviço:

```powershell
curl.exe http://127.0.0.1:8000/health
```

O health check informa os provedores configurados e os conjuntos de regras, mas
não revela chaves.

## 4. Executar uma análise

O conjunto inicial é `atestados-sistemas-operacionais-v1`. Ele é demonstração e
precisa ser homologado pelos especialistas antes de uso real.

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/analyses `
  -H "X-API-Key: $env:MOTOR_API_KEY" `
  -F "caso_id=PILOTO-001" `
  -F "requisito=Instalação, configuração e administração de Windows e Linux" `
  -F "conjunto_regras_id=atestados-sistemas-operacionais-v1" `
  -F "provedor=openai" `
  -F "documento=@C:\dados\atestado-sintetico.pdf;type=application/pdf"
```

Para verificação independente, adicione `-F "provedor_verificador=gemini"`. O
verificador deve ser diferente do provedor primário. Divergências de critério
forçam `REVISAO_HUMANA`; o sistema não tenta decidir por votação automática.

## 5. Conferir e revisar

Consulte a análise pelo `id` retornado:

```powershell
curl.exe http://127.0.0.1:8000/v1/analyses/ID_DA_ANALISE `
  -H "X-API-Key: $env:MOTOR_API_KEY"
```

O revisor deve abrir o PDF original e conferir requisito, regra, página, trecho,
critério e contexto. Depois registra sua decisão sem alterar a evidência original:

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/analyses/ID_DA_ANALISE/reviews `
  -H "Content-Type: application/json" `
  -H "X-API-Key: $env:MOTOR_API_KEY" `
  -d '{"decisao":"ATENDE_PARCIALMENTE","revisor":"analista.nome","justificativa":"A administração não está comprovada no trecho citado."}'
```

## 6. Alterar conhecimento

Os conjuntos ficam em `conhecimento/regras/`; templates, instruções e skills
ficam nas pastas correspondentes. Toda mudança deve:

1. possuir justificativa e responsável de negócio;
2. alterar a versão do conjunto;
3. incluir ou atualizar casos de regressão;
4. passar por Pull Request e aprovação humana;
5. executar novamente o benchmark antes de entrar em vigor.

Atestados reais e exemplos identificáveis não devem ser adicionados ao Git.

O mapa completo dos artefatos e o roteiro de perguntas para especialistas estão
em `INSUMOS_USUARIOS_PRODUTO.md`.

Para novos domínios, crie primeiro o conhecimento aprovado e depois conecte-o ao
motor por um novo ruleset JSON. O identificador do arquivo deve coincidir com o
campo `id` interno, e todas as referências de template, instructions e skills
devem existir antes da API aceitar o conjunto.

## 7. Retenção e expurgo

O conteúdo controlado pela solução deve ser removido em até 10 dias corridos
após a conclusão da análise. Isso inclui texto extraído, parecer integral,
evidências textuais, prompts, respostas, embeddings, caches, temporários e
backups operacionais. A confirmação de exportação permite exclusão antecipada.

Podem permanecer somente metadados mínimos sem conteúdo documental, como IDs,
hashes, versões, provedor/modelo, timestamps, classificação final, protocolo de
exportação e evidência do expurgo. O prazo desses metadados ainda deve ser
definido pelo proprietário dos dados.

A retenção de dados feita pelos provedores de IA segue suas políticas e os termos
aceitos pela organização. Ela não altera o prazo de 10 dias nos componentes do
produto e Zero Data Retention não é requisito de aceite.

A política completa está em `governanca/politicas/RETENCAO_DADOS.md`. A versão
`0.1` ainda não possui job automático de lifecycle; portanto, não deve receber
dados reais em ambiente compartilhado até que essa automação seja entregue.

## 8. Diagnóstico e logs

O motor grava eventos JSON Lines em stdout e, por padrão, em
`.motor-data/logs/motor.jsonl`. O arquivo é rotacionado diariamente e mantém 10
arquivos anteriores. Em produção, stdout deve ser coletado pela plataforma de
observabilidade e o prazo deve seguir a política aprovada para metadados.

Cada resposta HTTP possui o cabeçalho `X-Request-ID`. Use esse valor para reunir
todos os eventos de uma requisição sem procurar pelo conteúdo do documento.

Campos principais:

| Campo | Uso |
| --- | --- |
| `event` | Tipo estável do evento operacional |
| `request_id` | Correlação ponta a ponta da chamada |
| `stage` | Etapa em que o fluxo estava |
| `error_code` e `error_type` | Classificação da falha sem resposta sensível |
| `status_code` e `duration_ms` | Resultado e tempo da operação |
| `analysis_id`, `case_id` e `document_sha256` | Correlação por metadados |
| `provider`, `model` e tokens | Diagnóstico e custo da chamada de IA |
| `stack` | Arquivo, função e linha, sem mensagem ou variáveis locais |

Eventos de falha relevantes:

- `http_request_failed`: erro esperado de autenticação, validação ou domínio;
- `http_request_unhandled_exception`: falha inesperada com stack sanitizada;
- `provider_selection_failed`: provedor inválido ou sem credencial;
- `provider_call_failed`: timeout, limite, erro da API ou resposta inválida;
- `logging_file_configuration_failed`: arquivo de log indisponível.

Exemplo para consultar as falhas mais recentes no PowerShell:

```powershell
Get-Content .motor-data/logs/motor.jsonl -Tail 500 |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.level -in @("WARNING", "ERROR", "CRITICAL") }
```

Para procurar uma requisição específica:

```powershell
Select-String -Path .motor-data/logs/motor.jsonl* -SimpleMatch "REQUEST_ID"
```

Configuração:

```powershell
$env:MOTOR_ENVIRONMENT = "homologacao"
$env:MOTOR_LOG_LEVEL = "INFO"
$env:MOTOR_LOG_FILE = ".motor-data/logs/motor.jsonl"
$env:MOTOR_LOG_RETENTION_DAYS = "10"
```

Os logs nunca devem conter PDF, texto extraído, requisito, prompt, resposta
integral, justificativa do usuário ou chaves. A mensagem original de exceções
inesperadas também é omitida para impedir que respostas de terceiros vazem.

## 9. Limitações antes de produção

- não há OCR; PDFs sem texto são encaminhados como `ocr_necessario`;
- não há autenticação de usuário, apenas chave técnica da API;
- não há banco, object storage, fila, rate limiting ou isolamento por órgão;
- não há idempotência ou processamento concorrente por fila;
- não há RAG vetorial nesta etapa; o conjunto selecionado é enviado integralmente;
- o armazenamento local ainda não automatiza expurgo, confirmação de exportação
  nem tratamento de backups conforme a política de 10 dias;
- os logs locais são adequados ao piloto, mas ainda não há agregador, alertas,
  métricas, traces distribuídos ou integração com gestão de incidentes;
- a calibração dos modelos e regras ainda depende da massa descrita em
  `MASSA_TESTES_PRODUTO.md`;
- modelos configurados precisam ser homologados e fixados por versão.

Essas limitações restringem a versão 0.1 a ambiente local de piloto e dados
sintéticos ou formalmente autorizados.
