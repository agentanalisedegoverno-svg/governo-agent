import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from agente_governanca.coletor import montar_snapshot
from agente_governanca.governador import (
    consolidar_painel,
    consolidar_risco,
    fonte_autorizada,
    normalizar_provedores,
)
from agente_governanca.patches import validar_patch
from agente_governanca.provedores import (
    ProviderFailure,
    ProviderReview,
    _gemini_review,
    _openai_review,
)
from agente_governanca.verificacoes import verificar_secrets


class GitRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def write_and_track(self, path: str, content: str):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", path], check=True)


class CollectorTests(GitRepoTestCase):
    def test_snapshot_redacts_credentials(self):
        secret = "sk-ant-" + "a" * 22
        self.write_and_track("app.py", f'KEY = "{secret}"\n')
        snapshot, included = montar_snapshot(self.repo, ["app.py"])
        self.assertIn("app.py", included)
        self.assertNotIn(secret, snapshot)
        self.assertIn("[REDACTED]", snapshot)

    def test_snapshot_does_not_send_case_content_to_engineering_model(self):
        self.write_and_track("casos/PRIVATE/caso.json", '{"cpf": "00000000000"}\n')
        snapshot, included = montar_snapshot(self.repo, ["casos/PRIVATE/caso.json"])
        self.assertNotIn("00000000000", snapshot)
        self.assertNotIn("casos/PRIVATE/caso.json", included)
        self.assertIn("casos/PRIVATE/caso.json", snapshot)

    def test_deterministic_scanner_ignores_example_and_flags_real_secret(self):
        self.write_and_track(".env.example", "ANTHROPIC_API_KEY=sk-ant-...\n")
        secret = "sk-ant-" + "a" * 22
        self.write_and_track("settings.env", f"ANTHROPIC_API_KEY={secret}\n")
        findings = verificar_secrets(self.repo)
        self.assertEqual(1, len(findings))
        self.assertEqual(["settings.env"], findings[0]["affected_files"])


class PatchTests(unittest.TestCase):
    def test_accepts_normal_text_patch(self):
        diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1 @@
-old
+new
"""
        self.assertEqual(["README.md"], validar_patch(diff))

    def test_blocks_governor_self_modification(self):
        diff = """diff --git a/agente_governanca/governador.py b/agente_governanca/governador.py
--- a/agente_governanca/governador.py
+++ b/agente_governanca/governador.py
@@ -1 +1 @@
-old
+new
"""
        with self.assertRaisesRegex(ValueError, "autoalteracao"):
            validar_patch(diff)

    def test_blocks_path_traversal(self):
        diff = """diff --git a/README.md b/../outside.txt
--- a/README.md
+++ b/../outside.txt
@@ -1 +1 @@
-old
+new
"""
        with self.assertRaisesRegex(ValueError, "inseguro"):
            validar_patch(diff)


def _provider_payload() -> dict:
    return {
        "summary": "review",
        "overall_risk": "none",
        "decision": "pass",
        "findings": [],
        "architecture_decisions": [],
        "knowledge_updates": [{"title": "external"}],
        "proposed_patches": [{"title": "policy"}],
    }


class ProviderAdapterTests(unittest.TestCase):
    def test_openai_knowledge_pull_applies_domain_allowlist(self):
        captured = {}
        response = SimpleNamespace(
            output_text=json.dumps(_provider_payload()),
            model="test-openai",
            usage=SimpleNamespace(input_tokens=1, output_tokens=2),
        )
        client = SimpleNamespace(
            responses=SimpleNamespace(
                create=lambda **kwargs: captured.update(kwargs) or response
            )
        )
        fake_openai = ModuleType("openai")
        fake_openai.OpenAI = lambda: client

        with patch.dict(sys.modules, {"openai": fake_openai}):
            _openai_review("system", "user", {}, True, ["nist.gov"])

        self.assertEqual(
            ["nist.gov"], captured["tools"][0]["filters"]["allowed_domains"]
        )
        self.assertEqual("required", captured["tool_choice"])

    def test_gemini_knowledge_pull_discards_external_changes(self):
        interaction = SimpleNamespace(
            output_text=json.dumps(_provider_payload()),
            usage=SimpleNamespace(input_tokens=1, output_tokens=2),
        )
        fake_genai = ModuleType("google.genai")
        fake_genai.Client = lambda: SimpleNamespace(
            interactions=SimpleNamespace(create=lambda **_kwargs: interaction)
        )
        fake_google = ModuleType("google")
        fake_google.genai = fake_genai

        with patch.dict(
            sys.modules,
            {"google": fake_google, "google.genai": fake_genai},
        ):
            review = _gemini_review("system", "user", {}, True)

        self.assertEqual([], review.result["knowledge_updates"])
        self.assertEqual([], review.result["proposed_patches"])


class PolicyTests(unittest.TestCase):
    def test_provider_quorum_counts_unique_providers_only(self):
        providers = normalizar_provedores("openai,openai,gemini", 2)
        self.assertEqual(["openai", "gemini"], providers)

    def test_provider_quorum_rejects_impossible_configuration(self):
        with self.assertRaisesRegex(ValueError, "nao pode superar"):
            normalizar_provedores("openai,gemini", 3)

    def test_only_authorized_domains_and_subdomains_are_accepted(self):
        allowed = ["nist.gov", "docs.github.com"]
        self.assertTrue(fonte_autorizada("https://csrc.nist.gov/pubs", allowed))
        self.assertTrue(fonte_autorizada("https://docs.github.com/actions", allowed))
        self.assertFalse(fonte_autorizada("https://nist.gov.example.com/fake", allowed))

    def test_deterministic_critical_finding_overrides_ai_pass(self):
        result = {
            "overall_risk": "none",
            "decision": "pass",
            "findings": [{"severity": "critical"}],
        }
        consolidar_risco(result)
        self.assertEqual("critical", result["overall_risk"])
        self.assertEqual("changes_required", result["decision"])

    def test_panel_preserves_worst_risk_and_provider_origin(self):
        reviews = [
            ProviderReview(
                provider="openai",
                model="test-openai",
                usage={},
                result={
                    "summary": "OpenAI review",
                    "overall_risk": "low",
                    "decision": "pass_with_recommendations",
                    "findings": [],
                    "architecture_decisions": [],
                    "knowledge_updates": [],
                    "proposed_patches": [],
                },
            ),
            ProviderReview(
                provider="gemini",
                model="test-gemini",
                usage={},
                result={
                    "summary": "Gemini review",
                    "overall_risk": "high",
                    "decision": "changes_required",
                    "findings": [
                        {
                            "id": "SEC-1",
                            "title": "Risk",
                            "category": "security",
                            "severity": "high",
                            "confidence": "high",
                            "evidence": "Evidence",
                            "impact": "Impact",
                            "recommendation": "Fix",
                            "affected_files": ["app.py"],
                        }
                    ],
                    "architecture_decisions": [],
                    "knowledge_updates": [],
                    "proposed_patches": [],
                },
            ),
        ]
        result = consolidar_painel(reviews, [], [], minimum_providers=2)
        self.assertTrue(result["quorum"]["reached"])
        self.assertEqual("high", result["overall_risk"])
        self.assertEqual("ai:gemini", result["findings"][0]["origin"])

    def test_panel_reports_degraded_when_quorum_is_not_reached(self):
        failures = [
            ProviderFailure("anthropic", "missing_credentials", "missing"),
            ProviderFailure("gemini", "timeout", "timeout"),
        ]
        result = consolidar_painel([], failures, [], minimum_providers=2)
        self.assertFalse(result["quorum"]["reached"])
        self.assertEqual("degraded", result["execution_status"])


if __name__ == "__main__":
    unittest.main()
