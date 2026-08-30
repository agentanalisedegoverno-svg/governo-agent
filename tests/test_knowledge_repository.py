import json
import tempfile
import unittest
from pathlib import Path

from agente.documentos import blocos_documento_caso
from agente.seguranca import EntradaCasoInvalida, carregar_caso_json, resolver_caso
from conhecimento.validacao import markdowns_de_conhecimento, validar_markdown


BASE_DIR = Path(__file__).resolve().parent.parent


class KnowledgeRepositoryTests(unittest.TestCase):
    def test_markdowns_used_as_knowledge_have_valid_metadata(self):
        raiz = BASE_DIR / "conhecimento"
        paths = markdowns_de_conhecimento(raiz)
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.relative_to(raiz)):
                metadata = validar_markdown(path)
                self.assertIn(metadata.status, {"draft", "approved", "deprecated"})

    def test_metadata_schema_documents_required_fields(self):
        schema = json.loads(
            (BASE_DIR / "conhecimento" / "schemas" / "metadata.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("status", schema["required"])
        self.assertIn("authority", schema["properties"])

    def test_case_schema_documents_minimum_contract(self):
        schema = json.loads((BASE_DIR / "schemas" / "caso.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(["numero_processo", "objeto"], schema["required"])
        self.assertIn("estado_analise", schema["properties"])


class CaseInputSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.casos = Path(self.temp.name) / "casos"
        self.caso = self.casos / "CASO-001"
        self.caso.mkdir(parents=True)
        (self.caso / "caso.json").write_text(
            json.dumps(
                {
                    "numero_processo": "CASO-001",
                    "objeto": "Contratacao sintetica para teste do agente",
                }
            ),
            encoding="utf-8",
        )
        (self.caso / "edital.pdf").write_bytes(b"%PDF-sintetico")

    def tearDown(self):
        self.temp.cleanup()

    def test_resolver_caso_blocks_path_traversal(self):
        with self.assertRaises(EntradaCasoInvalida):
            resolver_caso(self.casos, "../CASO-001")

    def test_resolver_caso_accepts_existing_case(self):
        self.assertEqual(self.caso.resolve(), resolver_caso(self.casos, "CASO-001"))

    def test_documento_extra_blocks_path_traversal(self):
        with self.assertRaises(EntradaCasoInvalida):
            blocos_documento_caso(self.caso, [], "../fora.pdf")

    def test_glob_blocks_unsupported_type_before_provider(self):
        (self.caso / "segredo.txt").write_text("nao enviar", encoding="utf-8")
        with self.assertRaisesRegex(EntradaCasoInvalida, "Tipo de documento"):
            blocos_documento_caso(self.caso, ["*.txt"])

    def test_pdf_document_is_encoded(self):
        blocos = blocos_documento_caso(self.caso, ["edital.pdf"])
        self.assertEqual(1, len(blocos))
        self.assertEqual("application/pdf", blocos[0]["source"]["media_type"])

    def test_carregar_caso_json_rejects_directory_mismatch(self):
        (self.caso / "caso.json").write_text(
            json.dumps(
                {
                    "numero_processo": "OUTRO",
                    "objeto": "Contratacao sintetica para teste do agente",
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(EntradaCasoInvalida, "diverge"):
            carregar_caso_json(self.caso)


if __name__ == "__main__":
    unittest.main()

