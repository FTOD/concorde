import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


def load_builder():
    path = REPOSITORY_ROOT / "scripts/release/build-components.py"
    spec = importlib.util.spec_from_file_location("concorde_release_builder", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ReleaseArtifactTests(unittest.TestCase):
    def test_two_builds_are_byte_equivalent_and_catalogs_match(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            builder.build_release(Path(first), "http://127.0.0.1:8765")
            builder.build_release(Path(second), "http://127.0.0.1:8765")
            names = ["concorde-core-0.1.0.zip", "concorde-0.1.0.zip", "concorde-starter-0.1.0.zip"]
            for name in names:
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())
            self.assertEqual((Path(first) / "presets.json").read_bytes(), (Path(second) / "presets.json").read_bytes())

    def test_default_catalog_urls_are_https(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temporary:
            builder.build_release(Path(temporary), builder.DEFAULT_BASE_URL)
            for name in ("extensions.json", "presets.json", "bundles.json"):
                self.assertNotIn('"http://', (Path(temporary) / name).read_text())
                self.assertEqual(
                    json.loads((Path(temporary) / name).read_text()),
                    json.loads((REPOSITORY_ROOT / "catalogs" / name).read_text()),
                )


if __name__ == "__main__":
    unittest.main()
