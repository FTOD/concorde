import json
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


class EcosystemExplanationContractTests(unittest.TestCase):
    def test_installer_and_specs_agree_on_native_preview_apply(self):
        installer = (REPOSITORY_ROOT / "scripts/install-concorde.py").read_text()
        specifications = [
            (REPOSITORY_ROOT / "README.md").read_text(),
            (REPOSITORY_ROOT / "specs/concorde/modules/distribution/features/002-install-concorde.md").read_text(),
        ]
        for marker in ('FRAMEWORK_ROOT = ".concorde/framework"', 'RECEIPT_PATH = ".concorde/install.json"', "installation_plan", "apply_plan"):
            self.assertIn(marker, installer)
        for specification in specifications:
            for marker in ("scripts/install-concorde.py", "--target", "--integration", "--apply", "Profile 7", "Protocol 13"):
                self.assertIn(marker, specification)
            self.assertIn("preview", specification.lower())
            self.assertNotIn("specify-cli", specification)

    def test_public_specs_explain_authority_and_projection_boundaries(self):
        sources = [
            REPOSITORY_ROOT / "README.md",
            REPOSITORY_ROOT / "specs/concorde/architecture.md",
            REPOSITORY_ROOT / "specs/concorde/modules/understanding/architecture.md",
            REPOSITORY_ROOT / "specs/concorde/modules/capabilities/architecture.md",
            REPOSITORY_ROOT / "specs/concorde/modules/capabilities/features/004-maintain-agent-surfaces.md",
        ]
        combined = "\n".join(path.read_text().lower() for path in sources)
        for term in (
            "skills/", "operations/", "templates/", "src/concorde", "agent-assets", "concorde.json",
            "module", "architecture.md", "features/<nnn-name>.md", "code", "tests",
            "attempts/", "projection", "protocol 13", "cleanup-only", "ownership receipt",
        ):
            self.assertIn(term, combined, term)
        self.assertIn("standalone", combined)
        self.assertIn("no host", combined)

    def test_manifest_counts_match_documented_capability_and_template_counts(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        readme = (REPOSITORY_ROOT / "README.md").read_text()
        self.assertEqual(len(manifest["skills"]), 17)
        self.assertEqual(len(manifest["operations"]), 3)
        self.assertEqual(len(manifest["templates"]), 6)
        for skill in manifest["skills"]:
            self.assertTrue((REPOSITORY_ROOT / f"skills/{skill}/SKILL.md").is_file())
        for operation in manifest["operations"]:
            self.assertTrue((REPOSITORY_ROOT / f"operations/{operation}/SKILL.md").is_file())
            self.assertTrue((REPOSITORY_ROOT / f"operations/{operation}/operation.py").is_file())
        self.assertIn("17 packaged", (REPOSITORY_ROOT / "specs/concorde/modules/distribution/features/002-install-concorde.md").read_text())
        self.assertIn("17 packaged", (REPOSITORY_ROOT / "specs/concorde/modules/capabilities/features/002-provide-capability-surfaces.md").read_text())
        self.assertIn("$concorde-constitution", readme)


if __name__ == "__main__":
    unittest.main()
