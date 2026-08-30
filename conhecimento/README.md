# Conhecimento de Negócio Versionado

Este diretório contém o conhecimento confiável enviado ao motor:

- `regras/`: critérios estruturados, termos, exceções, fonte, versão e vigência;
- `templates/`: conteúdo e campos esperados no parecer;
- `instructions/`: comportamento geral, classificação e limites da análise;
- `skills/`: procedimentos especializados para localizar e validar evidências;
- `examples/`: somente exemplos sintéticos ou anonimizados e aprovados.

Na evolução do MVP, este diretório é o núcleo do Knowledge Repository. As próximas
pastas previstas são:

- `products/`: produtos, serviços, SLAs, implantação, limitações e regras
  comerciais reutilizáveis;
- `vendors/`: documentação técnica resumida de fabricantes, APIs e integrações,
  com referência ao documento-fonte;
- `checklists/`: listas de revisão para propostas, editais, arquitetura e
  validação de requisitos;
- `schemas/`: contratos JSON Schema para validar regras, requisitos,
  propostas, manifestos e metadata.

O atestado real e o requisito de uma demanda não ficam aqui. O atestado entra por
upload na API, e o requisito é um campo da requisição. PDFs reais usados em
avaliações permanecem em armazenamento controlado e são referenciados por hash.

Consulte `../INSUMOS_USUARIOS_PRODUTO.md` para saber o que solicitar aos
especialistas e `../MASSA_TESTES_PRODUTO.md` para dimensionar a homologação.

## Metadata recomendada

Arquivos Markdown usados como conhecimento reutilizável devem começar com:

```yaml
---
id: KNOWLEDGE-EXEMPLO-001
type: knowledge
domain: licitacoes
status: draft
version: 0.1
owner: area-responsavel
authority: knowledge
classification: internal
---
```

Use `status: approved` apenas depois de revisão humana. Para conflitos entre
fontes internas, aplique:

```text
policy > rule > standard > template > knowledge > example
```
