# Conhecimento de Negócio Versionado

Este diretório contém o conhecimento confiável enviado ao motor:

- `regras/`: critérios estruturados, termos, exceções, fonte, versão e vigência;
- `templates/`: conteúdo e campos esperados no parecer;
- `instructions/`: comportamento geral, classificação e limites da análise;
- `skills/`: procedimentos especializados para localizar e validar evidências;
- `examples/`: somente exemplos sintéticos ou anonimizados e aprovados.

O atestado real e o requisito de uma demanda não ficam aqui. O atestado entra por
upload na API, e o requisito é um campo da requisição. PDFs reais usados em
avaliações permanecem em armazenamento controlado e são referenciados por hash.

Consulte `../INSUMOS_USUARIOS_PRODUTO.md` para saber o que solicitar aos
especialistas e `../MASSA_TESTES_PRODUTO.md` para dimensionar a homologação.
