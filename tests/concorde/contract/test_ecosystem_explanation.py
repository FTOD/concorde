import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


class EcosystemExplanationContractTests(unittest.TestCase):
    def test_installer_and_public_guides_agree_on_profile_protocol_and_preview_apply(self):
        installer = (REPOSITORY_ROOT / "scripts/install-concorde.py").read_text(encoding="utf-8")
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        quick_start = (REPOSITORY_ROOT / "docs/quick-start.md").read_text(encoding="utf-8")

        self.assertIn('SPECIFY_VERSION = "0.16.4"', installer)
        self.assertIn('BUNDLE_ID = "concorde-bundle"', installer)
        self.assertIn("ARCHITECTURE_PROFILE = 7", installer)
        self.assertIn("WORKSPACE_PROTOCOL = 12", installer)
        for guide in (readme, quick_start):
            self.assertIn("scripts/install-concorde.py", guide)
            self.assertIn("--target", guide)
            self.assertIn("--integration", guide)
            self.assertIn("--preview", guide)
            self.assertIn("Omit", guide)
            self.assertIn("Profile 7", guide)
            self.assertIn("Protocol 12", guide)
        for operation in (
            '"init"',
            '"extension", "catalog", "add"',
            '"preset", "catalog", "add"',
            '"bundle", "catalog", "add"',
            '"bundle", "info"',
            '"bundle", "install"',
            '"bundle", "update"',
        ):
            self.assertIn(operation, installer)

    def test_package_explanations_name_ecosystem_roles_and_source_projection_boundary(self):
        sources = (
            REPOSITORY_ROOT / "README.md",
            REPOSITORY_ROOT / "presets/concorde/README.md",
            REPOSITORY_ROOT / "extensions/concorde/README.md",
            REPOSITORY_ROOT / "bundles/concorde-bundle/README.md",
            REPOSITORY_ROOT / "docs/self-hosting.md",
        )
        combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in sources)
        for term in (
            "spec kit", "bundle", "preset", "extension", "catalog", "coding-agent",
            "module", "architecture.md", "feature", "features/<nnn-name>.md", "code", "tests",
            "attempts/", "projection", "protocol 12",
        ):
            self.assertIn(term, combined, term)
        self.assertIn("canonical distribution sources", combined)
        self.assertIn("installed", combined)
        self.assertIn("cleanup-only", combined)

    def test_package_counts_and_descriptions_agree(self):
        preset = (REPOSITORY_ROOT / "presets/concorde/README.md").read_text(encoding="utf-8")
        extension = (REPOSITORY_ROOT / "extensions/concorde/README.md").read_text(encoding="utf-8")
        bundle = (REPOSITORY_ROOT / "bundles/concorde-bundle/README.md").read_text(encoding="utf-8")
        for body in (preset, bundle):
            self.assertIn("four templates", body.lower())
            self.assertIn("nine", body.lower())
            self.assertIn("fast-loop", body.lower())
        for body in (extension, bundle):
            self.assertIn("five", body.lower())
            self.assertIn("ask", body.lower())
            self.assertIn("deliver", body.lower())
        self.assertIn("Delivery Proposal 8", extension)
        self.assertIn("Architecture Source Profile 7", extension)


if __name__ == "__main__":
    unittest.main()
