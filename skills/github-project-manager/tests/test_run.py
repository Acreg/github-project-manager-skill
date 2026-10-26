import json
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run as workflow


class SourceSyncSkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "项目"
        (self.project / "v0.4.1").mkdir(parents=True)
        self.latest = self.project / "v0.4.2"
        (self.latest / "internal" / "httpadmin" / "webdist").mkdir(parents=True)
        (self.latest / "web" / "node_modules").mkdir(parents=True)
        (self.latest / "docs" / "plan").mkdir(parents=True)
        (self.project / "docs" / "plan").mkdir(parents=True)
        (self.project / "AGENTS.md").write_text("project instruction", encoding="utf-8")
        (self.project / ".env").write_text("DO_NOT_READ=topsecret", encoding="utf-8")
        (self.latest / "go.mod").write_text("module test\n", encoding="utf-8")
        (self.latest / "internal" / "httpadmin" / "webdist" / "index.html").write_text("<html>test</html>", encoding="utf-8")
        (self.latest / "web" / "node_modules" / "junk.js").write_text("dependency", encoding="utf-8")
        (self.latest / "README.md").write_text("# test", encoding="utf-8")
        (self.latest / "docs" / "plan" / "plan.md").write_text("# current", encoding="utf-8")
        (self.project / "docs" / "plan" / "v0.4.2-交接.md").write_text("# handoff", encoding="utf-8")
        (self.project / "v0.4.1" / "old.go").write_text("package main", encoding="utf-8")

    def test_latest_only_and_required_embedded_resources(self):
        result = workflow.main({"skill_action": "inspect", "project_dir": str(self.project)})
        self.assertTrue(result["ok"])
        self.assertEqual(result["version"], "v0.4.2")
        _, files = workflow.inventory(self.project, [])
        keys = {p.as_posix() for p in files}
        self.assertIn("v0.4.2/internal/httpadmin/webdist/index.html", keys)
        self.assertIn("v0.4.2/go.mod", keys)
        self.assertNotIn("v0.4.1/old.go", keys)
        self.assertNotIn(".env", keys)
        self.assertNotIn("v0.4.2/web/node_modules/junk.js", keys)

    def test_prepare_preserves_hashes_and_adds_docs(self):
        stage = self.root / "staging"
        result = workflow.main({
            "skill_action": "prepare",
            "project_dir": str(self.project),
            "output_dir": str(stage),
            "include_docs": ["docs/plan/v0.4.2-交接.md"],
        })
        self.assertTrue(result["ok"], result)
        self.assertTrue((stage / "v0.4.2" / "go.mod").exists())
        self.assertTrue((stage / "docs" / "plan" / "v0.4.2-交接.md").exists())
        self.assertFalse((stage / ".env").exists())
        manifest = json.loads((stage / "source-manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["original_files_unmodified"])
        self.assertTrue(all("sha256" in m for m in manifest["manifest"]))
        second = workflow.main({"skill_action": "prepare", "project_dir": str(self.project), "output_dir": str(stage)})
        self.assertFalse(second["ok"])
        self.assertEqual(second["code"], "OUTPUT_EXISTS")

    def test_secret_hit_reports_location_not_value(self):
        cfg = self.latest / "deploy"
        cfg.mkdir()
        secret = "not-for-printing-987654321"
        (cfg / "docker-compose.yml").write_text('SERVICE_MASTER_KEY: "' + secret + '"\n', encoding="utf-8")
        result = workflow.main({"skill_action": "inspect", "project_dir": str(self.project)})
        self.assertTrue(result["ok"])
        self.assertFalse(result["ready_for_upload_review"])
        findings = result["findings"]
        self.assertTrue(any(x["kind"] == "literal_config_secret" for x in findings))
        self.assertNotIn(secret, json.dumps(result, ensure_ascii=False))

    def test_bad_inputs(self):
        self.assertEqual(workflow.main({"skill_action": "unknown"})["code"], "UNKNOWN_ACTION")
        self.assertEqual(workflow.main({"skill_action": "inspect"})["code"], "PROJECT_REQUIRED")
        self.assertEqual(workflow.main({"skill_action": "prepare", "project_dir": str(self.project)})["code"], "OUTPUT_REQUIRED")
        self.assertEqual(workflow.main({
            "skill_action": "inspect", "project_dir": str(self.project),
            "include_docs": ["../elsewhere.md"]
        })["code"], "DOC_PATHS_INVALID")


if __name__ == "__main__":
    unittest.main()
