"""One test per row of the scaffold outcomes: each runs `concorde docsite` and checks the whole
envelope the row promises, its exit code included."""

from __future__ import annotations

import errno
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from concorde.distribution.cli import main
from concorde.distribution.project_defaults import install_project_defaults
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.verification import verifies
from concorde.spec.views import creation, docsite_scaffold
from tests.concorde.views.built_package import built_package

PROPOSAL = ".concorde/docsite-proposal.json"
# Spec core's command-line envelope maps each status to its exit code.
EXIT_CODES = {
    "success": 0,
    "proposal": 0,
    "unchanged": 0,
    "invalid": 1,
    "conflict": 2,
    "failed": 3,
}


class ScaffoldOutcomeTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        package = built_package()
        install_project_defaults(self.root, package)
        apply_project_proposal(
            self.root,
            package,
            project_proposal(self.root, package, "Atlas", "module.atlas"),
        )

    def docsite(self, *words: str) -> dict:
        """Run ``concorde docsite`` and return its envelope, checking its exit code."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["--project-root", str(self.root), "docsite", *words])
        envelope = json.loads(buffer.getvalue())
        self.assertEqual(EXIT_CODES[envelope["status"]], exit_code, envelope)
        self.assertEqual(
            ("docsite", ".", 4),
            (envelope["tool"], envelope["target"], envelope["schema_version"]),
        )
        return envelope

    def save_proposal(self) -> dict:
        """Propose, save the whole propose result as the accepted proposal, return the value."""
        proposed = self.docsite("--propose")
        self.assertEqual("proposal", proposed["status"], proposed)
        (self.root / PROPOSAL).write_text(json.dumps(proposed["result"]), "utf-8")
        return proposed["result"]["proposal"]

    def apply(self) -> dict:
        return self.docsite("--apply", "--proposal", PROPOSAL)

    def assert_refused(self, envelope: dict, rule: str, error: str | None) -> None:
        """An ``invalid`` row: empty result and artifacts, one error finding, the error code."""
        self.assertEqual("invalid", envelope["status"], envelope)
        self.assertEqual({}, envelope["result"])
        self.assertEqual([], envelope["artifacts"])
        self.assertEqual(
            [(rule, "error")],
            [(f["rule_id"], f["strictness"]) for f in envelope["findings"]],
        )
        self.assertEqual(error, (envelope["error"] or {}).get("code"))

    def assert_propose_findings(self, envelope: dict) -> None:
        """A 007 warning per missing or outdated prerequisite and, without a GitHub origin,
        the 009 info."""
        lacking = [
            item
            for item in envelope["result"]["prerequisites"]
            if item["status"] in {"missing", "outdated"}
        ]
        self.assertEqual(
            sorted(
                [("CONCORDE-DOCSITE-007", "warning")] * len(lacking)
                + [("CONCORDE-DOCSITE-009", "info")]
            ),
            sorted((f["rule_id"], f["strictness"]) for f in envelope["findings"]),
        )

    def proposed_paths(self, proposal: dict) -> list[str]:
        return sorted(item["path"] for item in proposal["files"])

    @verifies(
        "scenario.views.scaffold-outcomes", "scenario.views.scaffold-uninitialized"
    )
    def test_an_unreadable_configuration_is_invalid_001_for_both_commands(self):
        self.save_proposal()
        (self.root / ".concorde/config.json").unlink()
        for words in (["--propose"], ["--apply", "--proposal", PROPOSAL]):
            with self.subTest(command=words[0]):
                self.assert_refused(self.docsite(*words), "CONCORDE-DOCSITE-001", None)
        self.assertFalse((self.root / "docsite").exists())

    @verifies("scenario.views.scaffold-outcomes")
    def test_an_unusable_template_is_invalid_002_for_both_commands(self):
        self.save_proposal()
        package = self.root / "broken-package"
        package.mkdir()
        (package / "concorde.json").write_text(
            json.dumps({"package_roots": ["src"]}), "utf-8"
        )
        with mock.patch.object(
            docsite_scaffold, "_default_package_root", return_value=package
        ):
            for words in (["--propose"], ["--apply", "--proposal", PROPOSAL]):
                with self.subTest(command=words[0]):
                    self.assert_refused(
                        self.docsite(*words),
                        "CONCORDE-DOCSITE-002",
                        "invalid_docsite_template",
                    )
        self.assertFalse((self.root / "docsite").exists())

    @verifies("scenario.views.scaffold-outcomes")
    def test_a_malformed_option_is_invalid_003(self):
        envelope = self.docsite("--propose", "--base-url", "atlas", "--url", "ftp://x")
        self.assert_refused(envelope, "CONCORDE-DOCSITE-003", None)
        message = envelope["findings"][0]["message"]
        self.assertIn("--url", message)
        self.assertIn("--base-url", message)

    @verifies("scenario.views.scaffold-outcomes", "scenario.views.scaffold-propose")
    def test_a_new_scaffold_is_a_proposal_with_its_prerequisites(self):
        envelope = self.docsite("--propose")
        self.assertEqual("proposal", envelope["status"], envelope)
        self.assertEqual({"proposal", "prerequisites"}, set(envelope["result"]))
        self.assertEqual(
            ["node", "npm"],
            [item["name"] for item in envelope["result"]["prerequisites"]],
        )
        self.assertEqual([], envelope["artifacts"])
        self.assertIsNone(envelope["error"])
        self.assert_propose_findings(envelope)
        self.assertFalse((self.root / "docsite").exists())

    @verifies("scenario.views.scaffold-outcomes")
    def test_proposing_an_applied_scaffold_is_unchanged(self):
        proposal = self.save_proposal()
        self.assertEqual("success", self.apply()["status"])
        envelope = self.docsite("--propose")
        self.assertEqual("unchanged", envelope["status"], envelope)
        self.assertEqual({"proposal", "prerequisites"}, set(envelope["result"]))
        again = envelope["result"]["proposal"]
        paths = self.proposed_paths(proposal)
        self.assertEqual(
            {key: value for key, value in proposal.items() if key != "conflicts"},
            {key: value for key, value in again.items() if key != "conflicts"},
        )
        self.assertEqual(paths, [item["path"] for item in again["conflicts"]])
        self.assertEqual(paths, envelope["artifacts"])
        self.assertIsNone(envelope["error"])
        self.assert_propose_findings(envelope)

    @verifies("scenario.views.scaffold-outcomes")
    def test_apply_without_a_proposal_is_invalid_008(self):
        self.assert_refused(self.docsite("--apply"), "CONCORDE-DOCSITE-008", None)

    @verifies(
        "scenario.views.scaffold-outcomes", "scenario.views.scaffold-stale-rejected"
    )
    def test_an_unreadable_or_altered_proposal_is_invalid_004(self):
        for case in ("missing", "altered"):
            with self.subTest(case=case):
                if case == "altered":
                    proposal = self.save_proposal()
                    proposal["files"][0]["sha256"] = "sha256:" + "0" * 64
                    (self.root / PROPOSAL).write_text(json.dumps(proposal), "utf-8")
                envelope = self.apply()
                self.assert_refused(
                    envelope, "CONCORDE-DOCSITE-004", "invalid_proposal"
                )
                self.assertEqual(PROPOSAL, envelope["error"]["location"]["path"])
                self.assertFalse((self.root / "docsite").exists())

    @verifies(
        "scenario.views.scaffold-outcomes", "scenario.views.scaffold-apply-repeat"
    )
    def test_applying_an_applied_proposal_is_unchanged(self):
        proposal = self.save_proposal()
        self.assertEqual("success", self.apply()["status"])
        envelope = self.apply()
        self.assertEqual("unchanged", envelope["status"], envelope)
        self.assertEqual(
            {
                "identity": proposal["identity"],
                "template_digest": proposal["template_digest"],
                "github_pages": False,
            },
            envelope["result"],
        )
        self.assertEqual(self.proposed_paths(proposal), envelope["artifacts"])
        self.assertEqual([], envelope["findings"])
        self.assertIsNone(envelope["error"])

    @verifies("scenario.views.scaffold-outcomes", "scenario.views.scaffold-conflict")
    def test_an_existing_destination_is_a_conflict_naming_it(self):
        self.save_proposal()
        (self.root / "docsite").mkdir()
        (self.root / "docsite/package.json").write_bytes(b"{}\n")
        envelope = self.apply()
        self.assertEqual("conflict", envelope["status"], envelope)
        self.assertEqual({"conflicts": ["docsite/package.json"]}, envelope["result"])
        self.assertEqual([], envelope["artifacts"])
        self.assertEqual(
            [("CONCORDE-DOCSITE-005", "error", "docsite/package.json")],
            [
                (f["rule_id"], f["strictness"], f["source"])
                for f in envelope["findings"]
            ],
        )
        self.assertIsNone(envelope["error"])
        self.assertEqual(["package.json"], os.listdir(self.root / "docsite"))

    @verifies("scenario.views.scaffold-outcomes", "scenario.views.scaffold-apply")
    def test_a_new_scaffold_is_created_with_success(self):
        proposal = self.save_proposal()
        envelope = self.apply()
        self.assertEqual("success", envelope["status"], envelope)
        paths = self.proposed_paths(proposal)
        self.assertEqual(
            {
                "created": paths,
                "identity": proposal["identity"],
                "template_digest": proposal["template_digest"],
                "github_pages": False,
            },
            envelope["result"],
        )
        self.assertEqual(paths, envelope["artifacts"])
        self.assertEqual([], envelope["findings"])
        self.assertIsNone(envelope["error"])
        for path in paths:
            self.assertTrue((self.root / path).is_file(), path)

    @verifies(
        "scenario.views.scaffold-outcomes", "scenario.views.scaffold-concurrent-create"
    )
    def test_a_destination_that_appears_fails_naming_it_and_the_replaced_files(self):
        paths = self.proposed_paths(self.save_proposal())
        first, contested = paths[0], paths[-1]
        link = creation.os.link

        def concurrent(source, destination):
            if Path(destination) == self.root / contested:
                # Another process replaces the first file this application created, then
                # creates the last destination just before this application publishes it.
                replacement = self.root / "replacement"
                replacement.write_bytes(b"theirs\n")
                os.replace(replacement, self.root / first)
                Path(destination).write_bytes(b"created by another process\n")
            return link(source, destination)

        with mock.patch.object(creation.os, "link", side_effect=concurrent):
            envelope = self.apply()
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual(
            {"destination": contested, "replaced": [first]}, envelope["result"]
        )
        self.assertEqual([], envelope["artifacts"])
        self.assertEqual(
            [("CONCORDE-DOCSITE-006", "error", contested)],
            [
                (f["rule_id"], f["strictness"], f["source"])
                for f in envelope["findings"]
            ],
        )
        self.assertEqual("stale_proposal", envelope["error"]["code"])
        self.assertEqual(contested, envelope["error"]["location"]["path"])
        self.assertEqual(b"theirs\n", (self.root / first).read_bytes())
        self.assertEqual(
            b"created by another process\n", (self.root / contested).read_bytes()
        )
        for path in paths[1:-1]:
            self.assertFalse((self.root / path).exists(), path)

    @verifies("scenario.views.scaffold-outcomes", "scenario.views.scaffold-apply")
    def test_a_creation_that_fails_names_its_destination_and_removes_the_rest(self):
        paths = self.proposed_paths(self.save_proposal())
        failing = paths[len(paths) // 2]
        link = creation.os.link

        def fail(source, destination):
            if Path(destination) == self.root / failing:
                raise OSError(errno.EIO, "injected failure", destination)
            return link(source, destination)

        with mock.patch.object(creation.os, "link", side_effect=fail):
            envelope = self.apply()
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual({"destination": failing, "replaced": []}, envelope["result"])
        self.assertEqual(
            [("CONCORDE-DOCSITE-006", "error", failing)],
            [
                (f["rule_id"], f["strictness"], f["source"])
                for f in envelope["findings"]
            ],
        )
        self.assertEqual("system_error", envelope["error"]["code"])
        self.assertEqual(failing, envelope["error"]["causes"][0]["location"]["path"])
        for path in paths:
            self.assertFalse((self.root / path).exists(), path)


if __name__ == "__main__":
    unittest.main()
