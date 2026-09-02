from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


def _load(name: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, REPOSITORY_ROOT / "scripts/release" / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


publisher = _load("publish-release.py", "concorde_release_publisher_tests")
builder = _load("build-release.py", "concorde_release_builder_publisher_tests")


class FakeHost:
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
            (Path(directory) / name).write_bytes(self.files[name])


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
        return {name: (self.dist / name).read_bytes() for name in self.assets}

    @staticmethod
    def _mutating(host):
        return [call for call in host.calls if call[0] in {"create", "upload", "delete", "publish"}]

    def test_absent_release_is_drafted_uploaded_and_published(self):
        host = FakeHost()
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual((code, record["outcome"]), (0, "published"), record)
        self.assertEqual(host.calls[0], ("view", self.tag))
        self.assertEqual(host.calls[1], ("create", self.tag, False))
        self.assertEqual([call[2] for call in host.calls[2:-1]], self.assets)
        self.assertEqual(len(self.assets), 2)
        self.assertEqual(host.calls[-1], ("publish", self.tag))
        self.assertIn("Standalone Concorde package", host.notes)
        self.assertIn("install-concorde.py", host.notes)
        self.assertNotIn("specify bundle", host.notes)

    def test_dry_run_prints_plan_and_never_calls_host(self):
        host = FakeHost()
        record, code = publisher.publish(self.dist, self.tag, host, dry_run=True)
        self.assertEqual((code, record["outcome"]), (0, "dry-run"))
        self.assertEqual(host.calls, [])
        self.assertEqual(len(record["plan"]), 4)
        self.assertEqual(record["plan"][0], f"gh release create {self.tag} --draft --verify-tag")
        self.assertEqual(record["plan"][-1], f"gh release edit {self.tag} --draft=false")

    def test_tag_mismatch_is_rejected_before_host_call(self):
        host = FakeHost()
        record, code = publisher.publish(self.dist, "v9.9.9", host)
        self.assertEqual((code, record["outcome"]), (1, "version-mismatch"))
        self.assertEqual(host.calls, [])

    def test_verification_failure_publishes_nothing(self):
        archive = self.dist / builder.archive_name(self.version)
        archive.write_bytes(archive.read_bytes() + b"corrupt")
        host = FakeHost()
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual((code, record["outcome"]), (1, "verification-failed"))
        self.assertIn("digest", record["message"])
        self.assertEqual(host.calls, [])

    def test_prerelease_flag_is_forwarded_to_draft(self):
        original = publisher.is_prerelease
        publisher.is_prerelease = lambda version: True
        try:
            host = FakeHost()
            record, code = publisher.publish(self.dist, self.tag, host)
        finally:
            publisher.is_prerelease = original
        self.assertEqual(code, 0, record)
        self.assertEqual(host.calls[1], ("create", self.tag, True))
        self.assertIn("--prerelease", record["plan"][0])

    def test_leftover_draft_is_repaired(self):
        host = FakeHost(existing={"isDraft": True, "assets": [{"name": "old.zip"}, {"name": "release.json"}]})
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual((code, record["outcome"]), (0, "published"))
        self.assertEqual(host.calls[1:3], [("delete", self.tag, "old.zip"), ("delete", self.tag, "release.json")])
        self.assertNotIn("create", [call[0] for call in host.calls])

    def test_identical_published_release_is_noop(self):
        host = FakeHost(existing={"isDraft": False, "assets": []}, published_files=self._published_files())
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual((code, record["outcome"]), (0, "already-published"))
        self.assertTrue(record["compared"]["identical"])
        self.assertEqual(self._mutating(host), [])

    def test_divergent_published_release_is_refused(self):
        files = self._published_files()
        files["release.json"] += b"\n"
        host = FakeHost(existing={"isDraft": False, "assets": []}, published_files=files)
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual((code, record["outcome"]), (2, "divergent"))
        self.assertIn("release.json", record["compared"]["differences"])
        self.assertEqual(self._mutating(host), [])

    def test_missing_published_archive_is_divergent(self):
        files = self._published_files()
        del files[builder.archive_name(self.version)]
        host = FakeHost(existing={"isDraft": False, "assets": []}, published_files=files)
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual(code, 2)
        self.assertEqual(record["compared"]["differences"][builder.archive_name(self.version)], "missing from published release")

    def test_compare_only_never_mutates_absent_or_draft(self):
        for existing, outcome in ((None, "absent"), ({"isDraft": True, "assets": []}, "draft")):
            host = FakeHost(existing=existing)
            record, code = publisher.publish(self.dist, self.tag, host, compare_only=True)
            self.assertEqual((code, record["outcome"]), (0, outcome))
            self.assertEqual(self._mutating(host), [])

    def test_upload_failure_reports_residual_draft(self):
        failed_asset = self.assets[1]
        host = FakeHost(fail_on=("upload", failed_asset))
        record, code = publisher.publish(self.dist, self.tag, host)
        self.assertEqual((code, record["outcome"]), (1, "publication-failed"))
        self.assertEqual(record["residual_state"]["assets_uploaded"], self.assets[:1])
        self.assertNotIn(("publish", self.tag), host.calls)

    def test_pointer_has_one_archive_and_no_clock_or_host_component_fields(self):
        pointer = json.loads((self.dist / "release.json").read_text())
        self.assertEqual(pointer["schema_version"], 1)
        self.assertEqual(pointer["tag"], self.tag)
        self.assertEqual(pointer["architecture_profile"], 7)
        self.assertEqual(pointer["workspace_protocol"], 13)
        self.assertEqual(pointer["archive"]["name"], builder.archive_name(self.version))
        for removed in ("catalogs", "archives", "bundle_id", "speckit_version", "published_at"):
            self.assertNotIn(removed, pointer)

    def test_render_notes_names_native_archive_and_install(self):
        notes = publisher.render_notes("1.2.3", "https://example.test/v1.2.3", {"concorde-1.2.3.zip": "sha256:ab"})
        for needle in ("concorde-1.2.3.zip", "Architecture Profile", "Workspace Protocol", "install-concorde.py", "--apply"):
            self.assertIn(needle, notes)
        self.assertNotIn("preset", notes.lower())

    def test_cli_dry_run_and_version_mismatch_records(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = publisher.main(["--dist", str(self.dist), "--tag", self.tag, "--dry-run", "--gh", "/missing"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["outcome"], "dry-run")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = publisher.main(["--dist", str(self.dist), "--tag", "v9.9.9", "--gh", "/missing"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["outcome"], "version-mismatch")


if __name__ == "__main__":
    unittest.main()
