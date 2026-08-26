"""Regras deterministicas e verificacao de integridade das evidencias."""

from __future__ import annotations

import re
import unicodedata

from motor_atestados.modelos import (
    AvaliacaoCriterio,
    ConjuntoRegras,
    DocumentoExtraido,
    Evidencia,
    StatusCriterio,
)


def normalizar_texto(texto: str) -> str:
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    )
    return " ".join(sem_acentos.casefold().split())


def _trecho(texto: str, inicio: int, fim: int, margem: int = 180) -> str:
    esquerda = max(0, inicio - margem)
    direita = min(len(texto), fim + margem)
    return " ".join(texto[esquerda:direita].split())


def localizar_evidencias_exatas(
    documento: DocumentoExtraido, conjunto: ConjuntoRegras
) -> list[Evidencia]:
    evidencias: list[Evidencia] = []
    for criterio in conjunto.criterios:
        for pagina in documento.paginas:
            for termo in criterio.termos_aceitos:
                correspondencia = re.search(re.escape(termo), pagina.texto, re.IGNORECASE)
                if correspondencia:
                    evidencias.append(
                        Evidencia(
                            pagina=pagina.numero,
                            trecho=_trecho(
                                pagina.texto,
                                correspondencia.start(),
                                correspondencia.end(),
                            ),
                            criterios=[criterio.id],
                            verificada=True,
                            origem="regra",
                        )
                    )
                    break
    return evidencias


def avaliacao_deterministica(
    conjunto: ConjuntoRegras, evidencias: list[Evidencia]
) -> list[AvaliacaoCriterio]:
    encontrados = {criterio for evidencia in evidencias for criterio in evidencia.criterios}
    return [
        AvaliacaoCriterio(
            criterio_id=criterio.id,
            status=(
                StatusCriterio.ATENDIDO
                if criterio.id in encontrados
                else StatusCriterio.NAO_ATENDIDO
            ),
            justificativa=(
                "Termo aceito localizado diretamente no documento."
                if criterio.id in encontrados
                else "Nenhum termo aceito foi localizado pela verificacao deterministica."
            ),
        )
        for criterio in conjunto.criterios
    ]


def verificar_evidencias(
    documento: DocumentoExtraido,
    conjunto: ConjuntoRegras,
    evidencias: list[Evidencia],
) -> tuple[list[Evidencia], list[str]]:
    paginas = {pagina.numero: normalizar_texto(pagina.texto) for pagina in documento.paginas}
    criterios_validos = {criterio.id for criterio in conjunto.criterios}
    verificadas: list[Evidencia] = []
    alertas: list[str] = []

    for evidencia in evidencias:
        ids_validos = [item for item in evidencia.criterios if item in criterios_validos]
        pagina = paginas.get(evidencia.pagina, "")
        confere = bool(ids_validos) and normalizar_texto(evidencia.trecho) in pagina
        verificadas.append(
            evidencia.model_copy(
                update={"criterios": ids_validos or evidencia.criterios, "verificada": confere}
            )
        )
        if not confere:
            alertas.append(
                f"Evidencia da pagina {evidencia.pagina} nao confere com o texto extraido."
            )
    return verificadas, list(dict.fromkeys(alertas))
