import subprocess
import tempfile
import unittest
from pathlib import Path

from agente_governanca.coletor import montar_snapshot
from agente_governanca.governador import consolidar_risco, fonte_autorizada
from agente_governanca.patches import validar_patch
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


class PolicyTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
