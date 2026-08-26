# Manual do Motor Governado de Validação de Atestados

## 1. Escopo da versão 0.1

Esta versão recebe um requisito e um atestado em PDF, aplica um conjunto de
regras versionado, consulta um provedor de IA e devolve uma recomendação
estruturada com critérios, páginas, trechos e alertas. Toda análise exige revisão
humana antes de produzir uma decisão material.

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

## 7. Limitações antes de produção

- não há OCR; PDFs sem texto são encaminhados como `ocr_necessario`;
- não há autenticação de usuário, apenas chave técnica da API;
- não há banco, object storage, fila, rate limiting ou isolamento por órgão;
- não há idempotência ou processamento concorrente por fila;
- não há RAG vetorial nesta etapa; o conjunto selecionado é enviado integralmente;
- o armazenamento local não implementa retenção nem backup;
- a calibração dos modelos e regras ainda depende da massa descrita em
  `MASSA_TESTES_PRODUTO.md`;
- modelos configurados precisam ser homologados e fixados por versão.

Essas limitações restringem a versão 0.1 a ambiente local de piloto e dados
sintéticos ou formalmente autorizados.
