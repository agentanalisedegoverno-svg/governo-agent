# Politica de IA e Dados

## Componentes de IA

Modelos, prompts, agentes, ferramentas, MCPs, bases RAG e embeddings devem ter
proposito, proprietario, versao, dados permitidos, limites, avaliacao e estrategia
de rollback documentados. Saidas de IA que influenciem decisoes materiais devem
ser rastreaveis e sujeitas a revisao humana proporcional ao risco.

## Dados

- Aplicar minimizacao: enviar ao modelo somente o necessario para a tarefa.
- Redigir secrets e credenciais antes de qualquer chamada externa.
- Nao enviar dados pessoais ou sigilosos sem base legal e autorizacao registrada.
- Documentar classificacao, origem, finalidade, retencao, residencia e descarte.
- Restringir acesso pelo menor privilegio e registrar eventos relevantes.
- Avaliar vazamento, prompt injection, data poisoning e extracao de dados.

O governador de engenharia pode inventariar `casos/` e `normas/`, mas nao envia
o conteudo desses diretorios ao modelo. A analise documental possui pipeline
separado, finalidade especifica e controles proprios.

## Provedores

Dependencias de modelos e servicos externos devem registrar regiao, termos de uso,
retencao do provedor, controles de treinamento, custo, disponibilidade, limites e
plano de substituicao.
