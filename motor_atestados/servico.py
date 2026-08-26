"""Orquestracao do fluxo de analise e revisao humana."""

from __future__ import annotations

from uuid import uuid4

from motor_atestados.conhecimento import RepositorioConhecimento
from motor_atestados.excecoes import DocumentoInvalido
from motor_atestados.extracao import extrair_pdf
from motor_atestados.modelos import (
    AvaliacaoCriterio,
    EstadoAnalise,
    NivelConfianca,
    RegistroAnalise,
    RegistroRevisao,
    ResultadoAnalise,
    RevisaoHumanaEntrada,
    StatusCriterio,
)
from motor_atestados.observabilidade import atualizar_contexto, registrar_evento
from motor_atestados.provedores import executar_provedor, montar_entrada
from motor_atestados.regras import localizar_evidencias_exatas, verificar_evidencias
from motor_atestados.repositorio import RepositorioAnalises

MAX_REQUIREMENT_CHARS = 8_000
MAX_MODEL_CONTEXT_CHARS = 300_000


def _normalizar_avaliacoes(conjunto, parecer):
    esperados = {criterio.id for criterio in conjunto.criterios}
    recebidos = {item.criterio_id: item for item in parecer.criterios if item.criterio_id in esperados}
    avaliacoes = []
    alertas = []
    for criterio in conjunto.criterios:
        item = recebidos.get(criterio.id)
        if item is None:
            item = AvaliacaoCriterio(
                criterio_id=criterio.id,
                status=StatusCriterio.AMBIGUO,
                justificativa="O provedor nao avaliou este criterio.",
            )
            alertas.append(f"Criterio {criterio.id} ausente no parecer do provedor.")
        avaliacoes.append(item)
    desconhecidos = sorted({item.criterio_id for item in parecer.criterios} - esperados)
    if desconhecidos:
        alertas.append(f"Criterios desconhecidos descartados: {', '.join(desconhecidos)}.")
    return avaliacoes, alertas


def _classificar(conjunto, avaliacoes) -> ResultadoAnalise:
    por_id = {item.criterio_id: item.status for item in avaliacoes}
    obrigatorios = [por_id[criterio.id] for criterio in conjunto.criterios if criterio.obrigatorio]
    if any(status == StatusCriterio.AMBIGUO for status in obrigatorios):
        return ResultadoAnalise.REVISAO_HUMANA
    if obrigatorios and all(status == StatusCriterio.ATENDIDO for status in obrigatorios):
        return ResultadoAnalise.ATENDE
    if any(status in {StatusCriterio.ATENDIDO, StatusCriterio.PARCIAL} for status in obrigatorios):
        return ResultadoAnalise.ATENDE_PARCIALMENTE
    return ResultadoAnalise.NAO_ATENDE


def _divergencias(primario, verificador) -> list[str]:
    primario_por_id = {item.criterio_id: item.status for item in primario}
    verificador_por_id = {item.criterio_id: item.status for item in verificador}
    return sorted(
        criterio
        for criterio, status in primario_por_id.items()
        if verificador_por_id.get(criterio) != status
    )


class ServicoAtestados:
    def __init__(
        self,
        conhecimento: RepositorioConhecimento | None = None,
        repositorio: RepositorioAnalises | None = None,
        executor=executar_provedor,
    ):
        self.conhecimento = conhecimento or RepositorioConhecimento()
        self.repositorio = repositorio or RepositorioAnalises()
        self.executor = executor

    def analisar(
        self,
        *,
        caso_id: str,
        requisito: str,
        conjunto_regras_id: str,
        documento_nome: str,
        documento: bytes,
        provedor: str = "auto",
        provedor_verificador: str | None = None,
    ) -> RegistroAnalise:
        atualizar_contexto(
            stage="input_validation",
            case_id=caso_id,
            ruleset_id=conjunto_regras_id,
            provider=provedor if provedor in {"auto", "anthropic", "openai", "gemini"} else "invalid",
            document_size_bytes=len(documento),
            analysis_id=None,
            review_id=None,
            document_sha256=None,
            page_count=None,
            provider_role=None,
            model=None,
            result=None,
            confidence=None,
            review_required=None,
            alert_count=None,
        )
        registrar_evento("analysis_started")
        if not caso_id.strip() or len(caso_id) > 100 or any(c in caso_id for c in "/\\"):
            raise DocumentoInvalido("Identificador do caso invalido.")
        requisito = requisito.strip()
        if not requisito or len(requisito) > MAX_REQUIREMENT_CHARS:
            raise DocumentoInvalido(
                f"O requisito deve possuir entre 1 e {MAX_REQUIREMENT_CHARS} caracteres."
            )

        atualizar_contexto(stage="knowledge_load")
        conjunto = self.conhecimento.carregar_conjunto(conjunto_regras_id)
        atualizar_contexto(ruleset_version=conjunto.versao)
        registrar_evento("knowledge_loaded")

        atualizar_contexto(stage="pdf_extraction")
        extraido = extrair_pdf(documento_nome, documento)
        atualizar_contexto(
            document_sha256=extraido.sha256,
            page_count=len(extraido.paginas),
        )
        registrar_evento("pdf_extracted")

        atualizar_contexto(stage="prompt_assembly")
        instrucao = self.conhecimento.montar_instrucao(conjunto)
        entrada = montar_entrada(requisito, extraido, conjunto, instrucao)
        if len(entrada) > MAX_MODEL_CONTEXT_CHARS:
            raise DocumentoInvalido(
                "O documento excede o limite de contexto do piloto; divida-o ou use o pipeline de indexacao."
            )
        registrar_evento("model_input_assembled", input_chars=len(entrada))

        atualizar_contexto(stage="primary_provider", provider_role="primario")
        primario = self.executor(provedor, entrada, "primario")
        atualizar_contexto(
            provider=primario.execucao.provedor,
            model=primario.execucao.modelo,
        )
        avaliacoes, alertas = _normalizar_avaliacoes(conjunto, primario.parecer)

        atualizar_contexto(stage="evidence_verification")
        evidencias_ia, alertas_evidencias = verificar_evidencias(
            extraido, conjunto, primario.parecer.evidencias
        )
        alertas.extend(alertas_evidencias)
        evidencias = localizar_evidencias_exatas(extraido, conjunto) + evidencias_ia
        execucoes = [primario.execucao]

        divergentes: list[str] = []
        if provedor_verificador:
            if provedor_verificador == "auto":
                raise DocumentoInvalido("Informe explicitamente o provedor verificador.")
            if primario.execucao.provedor == provedor_verificador:
                raise DocumentoInvalido("O provedor verificador deve ser independente do primario.")
            atualizar_contexto(
                stage="verification_provider",
                provider=provedor_verificador,
                provider_role="verificador",
            )
            verificador = self.executor(provedor_verificador, entrada, "verificador")
            avaliacao_verificador, alertas_verificador = _normalizar_avaliacoes(
                conjunto, verificador.parecer
            )
            alertas.extend(alertas_verificador)
            divergentes = _divergencias(avaliacoes, avaliacao_verificador)
            if divergentes:
                alertas.append(
                    f"Provedores divergiram nos criterios: {', '.join(divergentes)}."
                )
            evidencias_verificador, alertas_verificacao = verificar_evidencias(
                extraido, conjunto, verificador.parecer.evidencias
            )
            evidencias.extend(evidencias_verificador)
            alertas.extend(alertas_verificacao)
            execucoes.append(verificador.execucao)

        # Uma afirmacao positiva sem ao menos uma citacao verificavel deve ser abstida.
        atualizar_contexto(stage="result_consolidation")
        criterios_com_evidencia = {
            criterio
            for evidencia in evidencias
            if evidencia.verificada
            for criterio in evidencia.criterios
        }
        sem_evidencia = [
            item.criterio_id
            for item in avaliacoes
            if item.status in {StatusCriterio.ATENDIDO, StatusCriterio.PARCIAL}
            and item.criterio_id not in criterios_com_evidencia
        ]
        if sem_evidencia:
            alertas.append(
                f"Conclusao positiva sem evidencia verificavel: {', '.join(sem_evidencia)}."
            )

        resultado = _classificar(conjunto, avaliacoes)
        if divergentes or sem_evidencia or any(not item.verificada for item in evidencias_ia):
            resultado = ResultadoAnalise.REVISAO_HUMANA

        confianca = primario.parecer.confianca
        if resultado == ResultadoAnalise.REVISAO_HUMANA:
            confianca = NivelConfianca.BAIXA

        registro = RegistroAnalise(
            id=str(uuid4()),
            caso_id=caso_id.strip(),
            requisito=requisito,
            conjunto_regras_id=conjunto.id,
            conjunto_regras_versao=conjunto.versao,
            documento_nome=extraido.nome,
            documento_sha256=extraido.sha256,
            resultado=resultado,
            confianca=confianca,
            criterios=avaliacoes,
            evidencias=evidencias,
            justificativa=primario.parecer.justificativa,
            revisao_humana_obrigatoria=True,
            alertas=list(dict.fromkeys(alertas)),
            provedores=execucoes,
        )
        atualizar_contexto(
            stage="analysis_persistence",
            analysis_id=registro.id,
            result=registro.resultado.value,
            confidence=registro.confianca.value,
            review_required=registro.revisao_humana_obrigatoria,
            alert_count=len(registro.alertas),
        )
        self.repositorio.salvar_analise(registro)
        registrar_evento(
            "analysis_completed",
            input_tokens=sum(item.input_tokens for item in execucoes),
            output_tokens=sum(item.output_tokens for item in execucoes),
        )
        return registro

    def obter(self, analise_id: str) -> EstadoAnalise:
        atualizar_contexto(stage="analysis_read", analysis_id=analise_id)
        return EstadoAnalise(
            analise=self.repositorio.obter_analise(analise_id),
            revisoes=self.repositorio.listar_revisoes(analise_id),
        )

    def revisar(self, analise_id: str, entrada: RevisaoHumanaEntrada) -> RegistroRevisao:
        atualizar_contexto(stage="human_review_validation", analysis_id=analise_id)
        self.repositorio.obter_analise(analise_id)
        if entrada.decisao in {
            ResultadoAnalise.REVISAO_HUMANA,
            ResultadoAnalise.ERRO_PROCESSAMENTO,
        }:
            raise ValueError("A revisao humana deve registrar uma decisao material.")
        revisao = RegistroRevisao(
            id=str(uuid4()),
            analise_id=analise_id,
            **entrada.model_dump(),
        )
        atualizar_contexto(stage="human_review_persistence", review_id=revisao.id)
        self.repositorio.salvar_revisao(revisao)
        registrar_evento("human_review_recorded", result=revisao.decisao.value)
        return revisao
