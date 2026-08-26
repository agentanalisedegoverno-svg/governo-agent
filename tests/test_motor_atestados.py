import io
import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from motor_atestados.conhecimento import RepositorioConhecimento
from motor_atestados.excecoes import DocumentoInvalido, ProvedorIndisponivel
from motor_atestados.extracao import extrair_pdf
from motor_atestados.modelos import (
    AvaliacaoCriterio,
    DocumentoExtraido,
    Evidencia,
    ExecucaoProvedor,
    NivelConfianca,
    PaginaDocumento,
    ParecerProvedor,
    ResultadoAnalise,
    RevisaoHumanaEntrada,
    StatusCriterio,
)
from motor_atestados.observabilidade import FormatadorJson, LOGGER_NAME
from motor_atestados.api import app
from motor_atestados.provedores import (
    RespostaProvedor,
    _anthropic,
    _gemini,
    _openai,
    executar_provedor,
)
from motor_atestados.regras import localizar_evidencias_exatas, verificar_evidencias
from motor_atestados.repositorio import RepositorioAnalises
from motor_atestados.servico import ServicoAtestados

RULESET = "atestados-sistemas-operacionais-v1"


def documento_extraido() -> DocumentoExtraido:
    return DocumentoExtraido(
        nome="atestado.pdf",
        sha256="a" * 64,
        paginas=[
            PaginaDocumento(
                numero=1,
                texto=(
                    "A empresa executou instalação e configuração de Windows e Linux, "
                    "incluindo suporte técnico aos usuários."
                ),
            )
        ],
    )


def parecer(status_administracao=StatusCriterio.NAO_ATENDIDO, com_evidencia=True):
    status = {
        "OS-INSTALACAO": StatusCriterio.ATENDIDO,
        "OS-CONFIGURACAO": StatusCriterio.ATENDIDO,
        "OS-ADMINISTRACAO": status_administracao,
        "OS-WINDOWS": StatusCriterio.ATENDIDO,
        "OS-LINUX": StatusCriterio.ATENDIDO,
    }
    evidencias = []
    if com_evidencia:
        evidencias.append(
            Evidencia(
                pagina=1,
                trecho="instalação e configuração de Windows e Linux",
                criterios=[
                    "OS-INSTALACAO",
                    "OS-CONFIGURACAO",
                    "OS-WINDOWS",
                    "OS-LINUX",
                ],
            )
        )
    return ParecerProvedor(
        resultado=ResultadoAnalise.ATENDE_PARCIALMENTE,
        confianca=NivelConfianca.ALTA,
        criterios=[
            AvaliacaoCriterio(
                criterio_id=criterio,
                status=valor,
                justificativa="Avaliação sintética para teste.",
            )
            for criterio, valor in status.items()
        ],
        evidencias=evidencias,
        justificativa="Administração não foi comprovada de forma explícita.",
    )


def resposta(papel, status_administracao=StatusCriterio.NAO_ATENDIDO, com_evidencia=True):
    return RespostaProvedor(
        parecer=parecer(status_administracao, com_evidencia),
        execucao=ExecucaoProvedor(
            provedor="openai" if papel == "primario" else "gemini",
            modelo="modelo-teste",
            papel=papel,
        ),
    )


class KnowledgeAndRuleTests(unittest.TestCase):
    def test_evaluation_manifest_schema_is_valid_json(self):
        schema_path = Path(__file__).resolve().parent.parent / "evals" / "schema-caso-teste.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual("object", schema["type"])
        self.assertIn("expected_result", schema["required"])

    def test_initial_ruleset_and_references_are_valid(self):
        repository = RepositorioConhecimento()
        ruleset = repository.carregar_conjunto(RULESET)
        self.assertEqual(5, len(ruleset.criterios))
        self.assertIn("Regra geral", repository.montar_instrucao(ruleset))

    def test_exact_evidence_keeps_page_and_criterion(self):
        ruleset = RepositorioConhecimento().carregar_conjunto(RULESET)
        evidences = localizar_evidencias_exatas(documento_extraido(), ruleset)
        ids = {item.criterios[0] for item in evidences}
        self.assertIn("OS-INSTALACAO", ids)
        self.assertNotIn("OS-ADMINISTRACAO", ids)
        self.assertTrue(all(item.pagina == 1 and item.verificada for item in evidences))

    def test_forged_quote_is_not_verified(self):
        ruleset = RepositorioConhecimento().carregar_conjunto(RULESET)
        evidence = Evidencia(
            pagina=1,
            trecho="administrou servidores Windows e Linux",
            criterios=["OS-ADMINISTRACAO"],
        )
        verified, alerts = verificar_evidencias(documento_extraido(), ruleset, [evidence])
        self.assertFalse(verified[0].verificada)
        self.assertTrue(alerts)

    def test_non_pdf_is_rejected_before_parser(self):
        with self.assertRaisesRegex(DocumentoInvalido, "assinatura PDF"):
            extrair_pdf("atestado.pdf", b"not-a-pdf")

    def test_digital_pdf_preserves_page_number_and_hash(self):
        import pymupdf

        pdf = pymupdf.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Atestado com instalacao e configuracao de Linux.")
        content = pdf.tobytes()
        pdf.close()

        extracted = extrair_pdf("atestado.pdf", content)
        self.assertEqual(1, extracted.paginas[0].numero)
        self.assertIn("Atestado", extracted.paginas[0].texto)
        self.assertEqual(64, len(extracted.sha256))


class ApiContractTests(unittest.TestCase):
    def test_business_endpoints_require_api_key(self):
        client = TestClient(app)
        with patch.dict(os.environ, {"MOTOR_API_KEY": "segredo-teste"}):
            self.assertEqual(401, client.get("/v1/rulesets").status_code)
            response = client.get(
                "/v1/rulesets", headers={"X-API-Key": "segredo-teste"}
            )
        self.assertEqual(200, response.status_code)
        self.assertIn(RULESET, response.json())

    def test_health_does_not_expose_keys(self):
        with patch.dict(
            os.environ,
            {"MOTOR_API_KEY": "nao-expor", "OPENAI_API_KEY": "tambem-nao-expor"},
        ):
            response = TestClient(app).get("/health")
        self.assertEqual(200, response.status_code)
        self.assertNotIn("nao-expor", response.text)
        self.assertNotIn("tambem-nao-expor", response.text)
        self.assertIn("openai", response.json()["provedores_configurados"])


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(FormatadorJson())
        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.handler.close()

    def events(self):
        return [json.loads(line) for line in self.stream.getvalue().splitlines()]

    def test_invalid_document_logs_stage_without_sensitive_content(self):
        segredo = "CONTEUDO-SENSIVEL-NAO-LOGAR"
        with patch.dict(os.environ, {"MOTOR_API_KEY": "segredo-teste"}):
            response = TestClient(app).post(
                "/v1/analyses",
                headers={"X-API-Key": "segredo-teste", "X-Request-ID": "req-teste-001"},
                data={
                    "caso_id": "CASO-LOG-001",
                    "requisito": segredo,
                    "conjunto_regras_id": RULESET,
                    "provedor": "openai",
                },
                files={"documento": ("atestado.pdf", segredo.encode(), "application/pdf")},
            )

        self.assertEqual(422, response.status_code)
        self.assertEqual("req-teste-001", response.headers["X-Request-ID"])
        falha = next(item for item in self.events() if item["event"] == "http_request_failed")
        self.assertEqual("pdf_extraction", falha["stage"])
        self.assertEqual("documento_invalido", falha["error_code"])
        self.assertNotIn(segredo, self.stream.getvalue())

    def test_unexpected_error_has_sanitized_stack_and_generic_response(self):
        segredo = "RESPOSTA-PRIVADA-DO-PROVEDOR"
        with patch.dict(os.environ, {"MOTOR_API_KEY": "segredo-teste"}), patch(
            "motor_atestados.api.servico.obter",
            side_effect=RuntimeError(segredo),
        ):
            response = TestClient(app, raise_server_exceptions=False).get(
                "/v1/analyses/analise-teste",
                headers={"X-API-Key": "segredo-teste", "X-Request-ID": "req-teste-002"},
            )

        self.assertEqual(500, response.status_code)
        self.assertEqual("erro_interno", response.json()["detail"]["codigo"])
        self.assertNotIn(segredo, response.text)
        evento = next(
            item
            for item in self.events()
            if item["event"] == "http_request_unhandled_exception"
        )
        self.assertEqual("req-teste-002", evento["request_id"])
        self.assertIn("RuntimeError", evento["error_chain"])
        self.assertTrue(evento["stack"])
        self.assertNotIn(segredo, self.stream.getvalue())

    def test_formatter_discards_fields_outside_allowlist(self):
        record = logging.LogRecord(
            LOGGER_NAME,
            logging.ERROR,
            __file__,
            1,
            "failure",
            (),
            None,
        )
        record.event = "test_failure"
        record.request_id = "req-safe"
        record.requisito = "REQUISITO-SECRETO"
        record.api_key = "EXAMPLE-CREDENTIAL-NOT-REAL"
        serializado = FormatadorJson().format(record)
        self.assertIn("req-safe", serializado)
        self.assertNotIn("REQUISITO-SECRETO", serializado)
        self.assertNotIn("EXAMPLE-CREDENTIAL-NOT-REAL", serializado)

    def test_provider_failure_does_not_expose_provider_response(self):
        segredo = "CORPO-SENSIVEL-RETORNADO-PELA-API"
        fake = ModuleType("openai")
        fake.OpenAI = lambda: SimpleNamespace(
            responses=SimpleNamespace(
                create=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError(segredo))
            )
        )
        with patch.dict(sys.modules, {"openai": fake}), patch.dict(
            os.environ, {"OPENAI_API_KEY": "teste"}
        ):
            with self.assertRaises(ProvedorIndisponivel) as capturada:
                executar_provedor("openai", "entrada sem dados reais", "primario")

        self.assertNotIn(segredo, str(capturada.exception))
        falha = next(item for item in self.events() if item["event"] == "provider_call_failed")
        self.assertEqual("provider_api_error", falha["error_code"])
        self.assertEqual("RuntimeError", falha["error_type"])
        self.assertNotIn(segredo, self.stream.getvalue())


class ProviderAdapterTests(unittest.TestCase):
    def test_openai_uses_strict_schema_and_disables_storage(self):
        captured = {}
        response = SimpleNamespace(
            output_text=parecer().model_dump_json(),
            model="openai-test",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )
        fake = ModuleType("openai")
        fake.OpenAI = lambda: SimpleNamespace(
            responses=SimpleNamespace(
                create=lambda **kwargs: captured.update(kwargs) or response
            )
        )
        with patch.dict(sys.modules, {"openai": fake}), patch.dict(
            os.environ, {"OPENAI_API_KEY": "teste"}
        ):
            result = _openai("entrada", "primario")
        self.assertFalse(captured["store"])
        self.assertTrue(captured["text"]["format"]["strict"])
        self.assertEqual("openai", result.execucao.provedor)

    def test_anthropic_uses_structured_output(self):
        captured = {}
        response = SimpleNamespace(
            content=[SimpleNamespace(type="text", text=parecer().model_dump_json())],
            model="anthropic-test",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )
        fake = ModuleType("anthropic")
        fake.Anthropic = lambda: SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: captured.update(kwargs) or response
            )
        )
        with patch.dict(sys.modules, {"anthropic": fake}), patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "teste"}
        ):
            result = _anthropic("entrada", "primario")
        self.assertEqual("json_schema", captured["output_config"]["format"]["type"])
        self.assertEqual("anthropic", result.execucao.provedor)

    def test_gemini_uses_json_schema_and_disables_storage(self):
        captured = {}
        response = SimpleNamespace(
            output_text=parecer().model_dump_json(),
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )
        fake_genai = ModuleType("google.genai")
        fake_genai.Client = lambda: SimpleNamespace(
            interactions=SimpleNamespace(
                create=lambda **kwargs: captured.update(kwargs) or response
            )
        )
        fake_google = ModuleType("google")
        fake_google.genai = fake_genai
        with patch.dict(
            sys.modules, {"google": fake_google, "google.genai": fake_genai}
        ), patch.dict(os.environ, {"GEMINI_API_KEY": "teste"}):
            result = _gemini("entrada", "verificador")
        self.assertFalse(captured["store"])
        self.assertEqual("application/json", captured["response_format"]["mime_type"])
        self.assertEqual("gemini", result.execucao.provedor)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repository = RepositorioAnalises(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def service(self, executor):
        return ServicoAtestados(repositorio=self.repository, executor=executor)

    @patch("motor_atestados.servico.extrair_pdf", return_value=documento_extraido())
    def test_partial_result_is_persisted_and_requires_human_review(self, _extract):
        service = self.service(lambda _name, _input, role: resposta(role))
        result = service.analisar(
            caso_id="CASO-001",
            requisito="Instalação, configuração e administração de Windows e Linux",
            conjunto_regras_id=RULESET,
            documento_nome="atestado.pdf",
            documento=b"%PDF-test",
            provedor="openai",
        )
        self.assertEqual(ResultadoAnalise.ATENDE_PARCIALMENTE, result.resultado)
        self.assertTrue(result.revisao_humana_obrigatoria)
        self.assertEqual(result.id, service.obter(result.id).analise.id)

        review = service.revisar(
            result.id,
            RevisaoHumanaEntrada(
                decisao=ResultadoAnalise.ATENDE_PARCIALMENTE,
                revisor="analista.teste",
                justificativa="A evidência foi conferida no documento sintético.",
            ),
        )
        self.assertEqual(result.id, review.analise_id)
        self.assertEqual(1, len(service.obter(result.id).revisoes))

    @patch("motor_atestados.servico.extrair_pdf", return_value=documento_extraido())
    def test_positive_conclusion_without_quote_abstains(self, _extract):
        service = self.service(
            lambda _name, _input, role: resposta(
                role, StatusCriterio.ATENDIDO, com_evidencia=False
            )
        )
        result = service.analisar(
            caso_id="CASO-002",
            requisito="Instalação, configuração e administração de Windows e Linux",
            conjunto_regras_id=RULESET,
            documento_nome="atestado.pdf",
            documento=b"%PDF-test",
            provedor="openai",
        )
        self.assertEqual(ResultadoAnalise.REVISAO_HUMANA, result.resultado)
        self.assertEqual(NivelConfianca.BAIXA, result.confianca)
        self.assertTrue(any("sem evidencia" in item for item in result.alertas))

    @patch("motor_atestados.servico.extrair_pdf", return_value=documento_extraido())
    def test_provider_disagreement_abstains(self, _extract):
        def executor(_name, _input, role):
            status = (
                StatusCriterio.NAO_ATENDIDO
                if role == "primario"
                else StatusCriterio.ATENDIDO
            )
            return resposta(role, status)

        result = self.service(executor).analisar(
            caso_id="CASO-003",
            requisito="Instalação, configuração e administração de Windows e Linux",
            conjunto_regras_id=RULESET,
            documento_nome="atestado.pdf",
            documento=b"%PDF-test",
            provedor="openai",
            provedor_verificador="gemini",
        )
        self.assertEqual(ResultadoAnalise.REVISAO_HUMANA, result.resultado)
        self.assertTrue(any("divergiram" in item for item in result.alertas))


if __name__ == "__main__":
    unittest.main()
