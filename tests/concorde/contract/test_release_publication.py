import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import jsonschema
import yaml

from tests.concorde.support.paths import REPOSITORY_ROOT

CONTRACT = (
    REPOSITORY_ROOT
    / "specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/contracts/release-publication.md"
)
WORKFLOW = REPOSITORY_ROOT / ".github/workflows/publish-release.yml"


def _load(name: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, REPOSITORY_ROOT / "scripts/release" / name)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def _contract_json_blocks() -> list[dict]:
    blocks = re.findall(r"```json\n(.*?)```", CONTRACT.read_text(encoding="utf-8"), re.S)
    return [json.loads(block) for block in blocks]


class ReleasePointerContractTests(unittest.TestCase):
    def setUp(self):
        self.schema, self.example = _contract_json_blocks()[:2]

    def test_contract_example_validates_against_its_schema(self):
        jsonschema.validate(self.example, self.schema)
        self.assertEqual(self.example["tag"], "v" + self.example["version"])
        self.assertTrue(all(url.startswith(self.example["base_url"] + "/") for url in self.example["catalogs"].values()))

    def test_generated_pointer_validates_and_matches_catalogs(self):
        builder = _load("build-components.py", "concorde_release_builder_pointer")
        publisher = _load("publish-release.py", "concorde_release_publisher_pointer")
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, ignore_errors=True)
        builder.build_release(temporary)
        identity = builder.read_release_identity()
        base_url = builder.default_base_url(identity.version)
        pointer = publisher.build_release_pointer(temporary, identity.version, f"v{identity.version}", base_url, identity.speckit_range)
        jsonschema.validate(pointer, self.schema)
        on_disk = json.loads((temporary / "release.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk, pointer)
        self.assertEqual(pointer["repository"], builder.REPOSITORY)
        self.assertEqual(pointer["speckit_version"], identity.speckit_range)
        for name, (collection, identifier) in {
            "extensions.json": ("extensions", "concorde"),
            "presets.json": ("presets", "concorde"),
            "bundles.json": ("bundles", "concorde-bundle"),
        }.items():
            catalog = json.loads((temporary / name).read_text(encoding="utf-8"))
            entry = catalog[collection][identifier]
            self.assertEqual(pointer["catalogs"][collection], catalog["catalog_url"])
            self.assertEqual(pointer["archives"][entry["download_url"].rsplit("/", 1)[1]], entry["sha256"])
        self.assertFalse({"published_at", "updated_at", "created_at"} & set(pointer))
        rebuilt = publisher.build_release_pointer(temporary, identity.version, f"v{identity.version}", base_url, identity.speckit_range)
        self.assertEqual(rebuilt, pointer)


class PublishWorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        self.triggers = self.workflow.get("on") or self.workflow.get(True)

    def test_workflow_triggers_on_version_tags_and_dispatch_with_dry_run(self):
        self.assertEqual(self.triggers["push"]["tags"], ["v*"])
        dry_run = self.triggers["workflow_dispatch"]["inputs"]["dry_run"]
        self.assertEqual(dry_run["type"], "boolean")
        self.assertTrue(dry_run["default"])

    def test_workflow_can_write_releases_and_serializes_per_ref(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "write"})
        self.assertIn("github.ref", self.workflow["concurrency"]["group"])

    def test_workflow_tests_builds_and_verifies_before_publishing(self):
        steps = self.workflow["jobs"]["publish"]["steps"]
        names = [step["name"] for step in steps]
        order = [
            next(i for i, name in enumerate(names) if "unit tests" in name.lower()),
            next(i for i, name in enumerate(names) if "contract tests" in name.lower()),
            next(i for i, name in enumerate(names) if name.lower().startswith("build")),
            next(i for i, name in enumerate(names) if name.lower().startswith("verify")),
            next(i for i, name in enumerate(names) if name.lower().startswith("publish")),
        ]
        self.assertEqual(order, sorted(order))
        publish_step = steps[order[-1]]
        self.assertIn("publish-release.py", publish_step["run"])
        self.assertNotIn("--clobber", publish_step["run"])
        verify_step = steps[order[-2]]
        self.assertIn("--expect-version", verify_step["run"])
        self.assertIn("--expect-base-url", verify_step["run"])


if __name__ == "__main__":
    unittest.main()
