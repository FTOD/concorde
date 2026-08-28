import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


def _load(name: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, REPOSITORY_ROOT / "scripts/release" / name)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class FakeHost:
    """Records every release-host operation; serves canned state for view/download."""

    def __init__(self, existing=None, published_files=None, fail_on=None):
        self.existing = existing
        self.files = published_files or {}
        self.fail_on = fail_on
        self.calls = []
        self.notes = None

    def _record(self, *call):
        self.calls.append(call)
        if self.fail_on and call[0] == self.fail_on[0] and (len(self.fail_on) == 1 or call[2] == self.fail_on[1]):
            raise publisher.PublicationError("host-error", f"simulated failure in {call[0]}")

    def view(self, tag):
        self._record("view", tag)
        return dict(self.existing) if self.existing is not None else None

    def create_draft(self, tag, notes_file, title, prerelease):
        self._record("create", tag, prerelease)
        self.notes = Path(notes_file).read_text(encoding="utf-8")

    def upload(self, tag, path):
        self._record("upload", tag, Path(path).name)

    def delete_asset(self, tag, name):
        self._record("delete", tag, name)

    def publish(self, tag):
        self._record("publish", tag)

    def download(self, tag, name, directory):
        self._record("download", tag, name)
        if name in self.files:
            (Path(directory) / name).write_text(self.files[name], encoding="utf-8")


publisher = _load("publish-release.py", "concorde_release_publisher")
builder = _load("build-components.py", "concorde_release_builder_for_publisher_tests")


class PublishReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporary, ignore_errors=True)
        self.dist = self.temporary / "dist"
        builder.build_release(self.dist)
        self.version = builder.read_release_version()
        self.tag = f"v{self.version}"
        self.assets = publisher.asset_names(self.version)

    def _published_files(self):
        record, code = publisher.publish(self.dist, self.tag, FakeHost(), dry_run=True)
        self.assertEqual(code, 0, record)
        return {name: (self.dist / name).read_text(encoding="utf-8") for name in ("extensions.json", "presets.json", "bundles.json", "release.json")}

    def _mutating(self, host):
        return [call for call in host.calls if call[0] in {"create", "upload", "delete", "publish"}]

    def test_absent_release_is_created_as_draft_uploaded_then_published(self):
        host = FakeHost(existing=None)
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 0, record)
        self.assertEqual(record["outcome"], "published")
        self.assertEqual(host.calls[0], ("view", self.tag))
        self.assertEqual(host.calls[1], ("create", self.tag, False))
        self.assertEqual([call[2] for call in host.calls[2:-1]], self.assets)
        self.assertEqual(len(self.assets), 7)
        self.assertIn("release.json", self.assets)
        self.assertEqual(host.calls[-1], ("publish", self.tag))
        self.assertTrue((self.dist / "release.json").is_file())
        self.assertIn(f"concorde-core@{self.version}", host.notes)
        self.assertIn(f"concorde@{self.version}", host.notes)
        self.assertIn(">=0.16.4,<0.16.5", host.notes)

    def test_dry_run_prints_plan_and_touches_no_host(self):
        host = FakeHost(existing=None)
        record, code = publisher.publish(self.dist, self.tag, host, dry_run=True)
        self.assertEqual(code, 0)
        self.assertEqual(record["outcome"], "dry-run")
        self.assertEqual(host.calls, [])
        self.assertEqual(record["plan"][0], f"gh release create {self.tag} --draft --verify-tag")
        self.assertEqual(record["plan"][-1], f"gh release edit {self.tag} --draft=false")
        self.assertEqual(len(record["plan"]), 9)
        self.assertEqual(record["base_url"], f"https://github.com/FTOD/concorde/releases/download/{self.tag}")
        self.assertIn(f"concorde-core@{self.version}", record["notes"])

    def test_tag_that_disagrees_with_manifest_version_is_rejected(self):
        host = FakeHost()
        record, code = publisher.publish(self.dist, "v9.9.9", host)
        self.assertEqual(code, 1)
        self.assertEqual(record["outcome"], "version-mismatch")
        self.assertIn("v9.9.9", record["message"])
        self.assertIn(self.version, record["message"])
        self.assertEqual(host.calls, [])

    def test_verification_failure_publishes_nothing(self):
        catalog = self.dist / "bundles.json"
        text = catalog.read_text(encoding="utf-8")
        catalog.write_text(text.replace('"sha256:', '"sha256:0'), encoding="utf-8")
        host = FakeHost()
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 1)
        self.assertEqual(record["outcome"], "verification-failed")
        self.assertIn("digest mismatch", record["message"])
        self.assertEqual(host.calls, [])

    def test_prerelease_version_marks_release_and_pointer(self):
        self.assertTrue(publisher.is_prerelease("0.3.0-rc.1"))
        self.assertFalse(publisher.is_prerelease("0.3.0"))
        original = publisher.is_prerelease
        publisher.is_prerelease = lambda version: True
        try:
            host = FakeHost(existing=None)
            record, code = publisher.publish(self.dist, self.tag, host)
        finally:
            publisher.is_prerelease = original
        self.assertEqual(code, 0, record)
        self.assertEqual(host.calls[1], ("create", self.tag, True))
        self.assertIn("--prerelease", record["plan"][0])
        self.assertTrue(json.loads((self.dist / "release.json").read_text(encoding="utf-8"))["prerelease"])

    def test_leftover_draft_is_repaired_and_published(self):
        host = FakeHost(existing={"isDraft": True, "assets": [{"name": "presets.json"}, {"name": "concorde-0.1.0.zip"}]})
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 0, record)
        self.assertEqual(record["outcome"], "published")
        self.assertNotIn("create", [call[0] for call in host.calls])
        self.assertEqual(host.calls[1:3], [("delete", self.tag, "presets.json"), ("delete", self.tag, "concorde-0.1.0.zip")])
        self.assertEqual([call[2] for call in host.calls[3:-1]], self.assets)
        self.assertEqual(host.calls[-1], ("publish", self.tag))

    def test_identical_published_release_is_a_noop(self):
        files = self._published_files()
        host = FakeHost(existing={"isDraft": False, "assets": []}, published_files=files)
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 0, record)
        self.assertEqual(record["outcome"], "already-published")
        self.assertTrue(record["compared"]["identical"])
        self.assertEqual(self._mutating(host), [])

    def test_divergent_published_release_is_refused(self):
        files = self._published_files()
        files["presets.json"] = files["presets.json"].replace('"sha256:', '"sha256:f')
        host = FakeHost(existing={"isDraft": False, "assets": []}, published_files=files)
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 2)
        self.assertEqual(record["outcome"], "divergent")
        self.assertEqual(sorted(record["compared"]["differences"]), ["presets.json"])
        self.assertIn("sha256", record["compared"]["differences"]["presets.json"])
        self.assertEqual(self._mutating(host), [])

    def test_missing_published_asset_counts_as_divergent(self):
        files = self._published_files()
        del files["release.json"]
        host = FakeHost(existing={"isDraft": False, "assets": []}, published_files=files)
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 2)
        self.assertEqual(record["compared"]["differences"]["release.json"], "missing from the published release")

    def test_compare_only_never_mutates(self):
        host = FakeHost(existing=None)
        record, code = publisher.publish(self.dist, self.tag, host, compare_only=True)
        self.assertEqual((code, record["outcome"]), (0, "absent"))
        self.assertEqual(self._mutating(host), [])
        host = FakeHost(existing={"isDraft": True, "assets": []})
        record, code = publisher.publish(self.dist, self.tag, host, compare_only=True)
        self.assertEqual((code, record["outcome"]), (0, "draft"))
        self.assertEqual(self._mutating(host), [])

    def test_upload_failure_reports_residual_draft_state(self):
        host = FakeHost(existing=None, fail_on=("upload", "presets.json"))
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 1)
        self.assertEqual(record["outcome"], "publication-failed")
        self.assertEqual(record["residual_state"]["draft"], self.tag)
        self.assertEqual(record["residual_state"]["assets_uploaded"], self.assets[: self.assets.index("presets.json")])
        self.assertNotIn(("publish", self.tag), host.calls)

    def test_pointer_has_no_clock_fields_and_matches_catalog_digests(self):
        self._published_files()
        pointer = json.loads((self.dist / "release.json").read_text(encoding="utf-8"))
        self.assertEqual(pointer["schema_version"], "1.0")
        self.assertEqual(pointer["tag"], self.tag)
        self.assertNotIn("published_at", pointer)
        self.assertNotIn("updated_at", pointer)
        for name, (collection, identifier) in {
            "extensions.json": ("extensions", "concorde"),
            "presets.json": ("presets", "concorde-core"),
            "bundles.json": ("bundles", "concorde-bundle"),
        }.items():
            catalog = json.loads((self.dist / name).read_text(encoding="utf-8"))
            entry = catalog[collection][identifier]
            self.assertEqual(pointer["archives"][Path(entry["download_url"]).name], entry["sha256"])
            self.assertEqual(pointer["catalogs"][collection], catalog["catalog_url"])

    def test_render_notes_names_components_range_and_registration_commands(self):
        notes = publisher.render_notes("0.1.0", ">=0.16.4,<0.16.5", "https://github.com/FTOD/concorde/releases/download/v0.1.0", {"concorde-0.1.0.zip": "sha256:ab"})
        for needle in ("concorde-core@0.1.0", "concorde@0.1.0", "concorde-bundle@0.1.0", ">=0.16.4,<0.16.5", "specify bundle install concorde-bundle", "releases/latest/download/release.json"):
            self.assertIn(needle, notes)

    def test_cli_dry_run_prints_record_and_exit_code(self):
        import contextlib
        import io

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = publisher.main(["--dist", str(self.dist), "--tag", self.tag, "--dry-run", "--gh", "/nonexistent/gh"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["outcome"], "dry-run")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = publisher.main(["--dist", str(self.dist), "--tag", "v9.9.9", "--gh", "/nonexistent/gh"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["outcome"], "version-mismatch")


if __name__ == "__main__":
    unittest.main()
