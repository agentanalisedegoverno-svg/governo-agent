# Política de Retenção e Expurgo de Dados

## 1. Regra aprovada

A solução não deve manter documentos, textos extraídos, prompts, respostas
integrais, embeddings, evidências textuais, arquivos temporários ou rascunhos
por mais de **10 dias corridos após a conclusão da análise**.

O prazo se aplica somente aos componentes controlados pelo projeto. A retenção
realizada por Claude/Anthropic, OpenAI, Gemini/Google ou outro terceiro segue os
termos e as políticas do provedor contratualmente aceitos pela organização. Zero
Data Retention não é requisito de aceite deste produto.

Configurações de minimização, como desabilitar armazenamento opcional quando a
API oferecer esse controle, devem permanecer habilitadas sempre que não
prejudicarem o funcionamento homologado.

## 2. Dados sujeitos ao prazo de 10 dias

- PDF e demais documentos enviados pelo usuário;
- texto extraído, OCR e representações intermediárias;
- prompt montado e contexto enviado ao provedor;
- resposta integral do provedor e parecer detalhado local;
- páginas, trechos e evidências que reproduzam o documento;
- embeddings, índices, caches, filas, arquivos temporários e backups desses dados;
- proposta ou rascunho local depois que o resultado for encaminhado ao destino.

O PDF do piloto atual é processado em memória e não é persistido. Os registros
integrais em `.motor-data/` continuam sujeitos a esta política.

## 3. Marco temporal e operação

1. A conclusão da análise deve registrar `completed_at` e calcular `expires_at`
   como, no máximo, `completed_at + 10 dias`.
2. A confirmação de exportação permite expurgo antecipado, mas nunca prorroga
   `expires_at`.
3. Em D+7, a operação deve alertar sobre resultados ainda não exportados.
4. Em D+9, a pendência deve ser escalada ao responsável do produto.
5. Em D+10, os dados sujeitos a expurgo devem ser removidos dos armazenamentos
   ativos, temporários, índices e backups operacionais alcançados pela política.
6. Cada execução deve gerar evidência sem reproduzir o conteúdo excluído.

Uma falha de expurgo deve gerar alerta operacional e incidente rastreável. Não
deve resultar em extensão silenciosa do prazo.

## 4. Metadados mínimos de auditoria

Podem permanecer fora do prazo de 10 dias, sem conteúdo documental:

- identificadores da análise, caso e organização;
- hashes dos documentos e do resultado exportado;
- classificação final e indicação de revisão humana;
- provedor, modelo e contagem de tokens;
- versões do conjunto de regras, template, instructions e skills;
- datas de recebimento, conclusão, exportação e expurgo;
- identificador do destino externo e protocolo de confirmação;
- resultado da rotina de expurgo e eventual exceção aprovada.

O prazo desses metadados deve ser definido pelo proprietário dos dados conforme
a política arquivística aplicável. Até essa definição, dados reais não devem ser
usados fora de um piloto formalmente autorizado.

## 5. Exceções

Guarda legal, investigação ou outra exceção deve registrar proprietário,
justificativa, escopo, base aplicável, controles de acesso e data de expiração.
Somente uma pessoa autorizada pode aprovar a exceção. O agente e a rotina de
expurgo não podem criar ou renovar uma exceção autonomamente.

## 6. Responsabilidades dos componentes

| Componente | Responsabilidade |
| --- | --- |
| API | Classificar os dados e registrar os marcos do ciclo de vida |
| Object storage | Aplicar lifecycle de no máximo 10 dias aos objetos temporários |
| Banco de dados | Separar conteúdo expirável de metadados mínimos de auditoria |
| Fila e workers | Não transportar documento integral quando um identificador for suficiente |
| Índice/RAG | Permitir exclusão por análise e ser reconstruível |
| Observabilidade | Não registrar documentos, prompts ou respostas integrais |
| Operação | Monitorar D+7, D+9, D+10, falhas e exceções |
| Provedor externo | Aplicar seus próprios termos de retenção aceitos pela organização |

## 7. Estado de implementação

Esta política está versionada, mas o expurgo automático ainda não foi
implementado na versão `0.1`. Antes de usar dados reais em ambiente
compartilhado, o produto deve implementar `completed_at`, `expires_at`,
confirmação de exportação, job idempotente de expurgo, evidências e testes de
restauração para comprovar que backups não reintroduzem conteúdo expirado.

Logs operacionais contêm somente metadados permitidos e possuem rotação local
configurada em 10 dias por padrão. O proprietário dos dados deve aprovar o prazo
definitivo da plataforma central de observabilidade.
