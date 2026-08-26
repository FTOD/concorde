import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject

import importlib.util

_builder_spec = importlib.util.spec_from_file_location("concorde_release_builder", REPOSITORY_ROOT / "scripts/release/build-components.py")
assert _builder_spec and _builder_spec.loader
_builder = importlib.util.module_from_spec(_builder_spec)
_builder_spec.loader.exec_module(_builder)


class StarterJourneyAcceptance(unittest.TestCase):
    def test_installed_proposal_context_validation_and_repeatability(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dist = root / "dist"
            project_root = root / "project"
            with CatalogServer(dist) as server:
                _builder.build_release(dist, server.base_url)
                project = SpecifyProject(project_root)
                project.initialize()
                project.register_catalogs(server.base_url)
                project.run("bundle", "install", "concorde-bundle")
                launcher = project_root / ".specify/extensions/concorde/scripts/bash/concorde.sh"

                def runtime(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
                    result = subprocess.run([str(launcher), *arguments], cwd=project_root, capture_output=True, text=True)
                    if check and result.returncode:
                        self.fail(result.stdout + result.stderr)
                    return result

                proposed_result = runtime("init", "--propose", "--module-id", "module.sample", "--name", "Sample")
                proposal_envelope = json.loads(proposed_result.stdout)
                self.assertEqual(proposal_envelope["status"], "proposal")
                self.assertFalse((project_root / ".concorde/config.json").exists())
                (project_root / "accepted.json").write_text(json.dumps(proposal_envelope["result"]["proposal"]))
                applied = json.loads(runtime("init", "--apply", "--proposal", "accepted.json").stdout)
                self.assertEqual(applied["status"], "success")
                unchanged = json.loads(runtime("init", "--apply", "--proposal", "accepted.json").stdout)
                self.assertEqual(unchanged["status"], "unchanged")
                context = json.loads(runtime("context", "module.sample", "--format", "json").stdout)
                self.assertEqual(context["status"], "success")
                self.assertEqual(context["result"]["context"]["children"], [])
                validations = [runtime("validate", "--format", "json").stdout for _ in range(3)]
                self.assertEqual(validations[0], validations[1])
                self.assertEqual(validations[1], validations[2])
                self.assertEqual(json.loads(validations[0])["status"], "success")
                module = project_root / "specs/sample/module.md"
                module.write_text(module.read_text().replace("features: []", "features:\n  - feature.sample.missing"))
                invalid = runtime("validate", "--format", "json", check=False)
                self.assertEqual(invalid.returncode, 1)
                self.assertIn("CONCORDE-REF-001", invalid.stdout)

    def test_installed_update_and_safe_removal_journey(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dist = root / "dist"
            project_root = root / "project"
            with CatalogServer(dist) as server:
                _builder.build_release(dist, server.base_url)
                project = SpecifyProject(project_root)
                project.initialize()
                project.register_catalogs(server.base_url)
                project.run("bundle", "install", "concorde-bundle")
                (project_root / ".concorde").mkdir()
                (project_root / ".concorde/config.json").write_text('{"maintainer":"owned"}\n')
                (project_root / "specs/example").mkdir(parents=True)
                (project_root / "specs/example/intent.md").write_text("# Intent\n")
                source_hashes = project.source_hashes()
                _builder.build_release(dist, server.base_url, "0.1.1")
                project.clear_catalog_caches()
                project.run("bundle", "update", "concorde-bundle")
                self.assertEqual(project.json("bundle", "list", "--json")[0]["version"], "0.1.1")
                project.run("bundle", "remove", "concorde-bundle")
                self.assertEqual(project.source_hashes(), source_hashes)


if __name__ == "__main__":
    unittest.main()
