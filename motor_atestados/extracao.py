"""Extracao local e limitada de PDFs, preservando pagina e hash."""

from __future__ import annotations

import hashlib

from motor_atestados.excecoes import DocumentoInvalido, OcrNecessario
from motor_atestados.modelos import DocumentoExtraido, PaginaDocumento

MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
MAX_PAGES = 300
MIN_EXTRACTED_CHARS = 20


def extrair_pdf(nome: str, conteudo: bytes) -> DocumentoExtraido:
    if not nome.lower().endswith(".pdf"):
        raise DocumentoInvalido("Somente arquivos PDF sao aceitos.")
    if not conteudo.startswith(b"%PDF-"):
        raise DocumentoInvalido("O conteudo enviado nao possui assinatura PDF valida.")
    if not conteudo or len(conteudo) > MAX_DOCUMENT_BYTES:
        raise DocumentoInvalido(
            f"O PDF deve possuir no maximo {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB."
        )

    try:
        import pymupdf

        documento = pymupdf.open(stream=conteudo, filetype="pdf")
    except Exception as exc:
        raise DocumentoInvalido("Nao foi possivel abrir o PDF.") from exc

    try:
        if documento.page_count < 1 or documento.page_count > MAX_PAGES:
            raise DocumentoInvalido(f"O PDF deve possuir entre 1 e {MAX_PAGES} paginas.")
        paginas = [
            PaginaDocumento(numero=i + 1, texto=documento.load_page(i).get_text("text"))
            for i in range(documento.page_count)
        ]
    finally:
        documento.close()

    if sum(len(p.texto.strip()) for p in paginas) < MIN_EXTRACTED_CHARS:
        raise OcrNecessario(
            "O PDF nao possui texto extraivel suficiente; encaminhe para o pipeline de OCR."
        )

    return DocumentoExtraido(
        nome=nome,
        sha256=hashlib.sha256(conteudo).hexdigest(),
        paginas=paginas,
    )
