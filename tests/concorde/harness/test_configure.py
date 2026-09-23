"""concorde-configure proposes a digest-bound configuration change and applies exactly that proposal."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.project_defaults import (
    PROTOCOL_MANIFEST_PATH,
    protocol_files,
)
from concorde.harness import configure
from concorde.harness.configuration import load_configuration
from concorde.harness.host import OperationHost
from concorde.operations.dispatch import run_operation
from concorde.spec.initialize import protocol_binding
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.repository import digest as digest_bytes
from concorde.spec.typed_data import TypedDataError, typed, validate_typed
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import PACKAGE, project
from tests.concorde.support.operation_json import CONFIGURATION


def configuration(**data) -> dict:
    return {
        "type_id": "concorde-operation-configuration",
        "schema_version": 2,
        "data": data,
    }


SELECTION = configuration(
    model="anthropic/claude-sonnet-5",
    thinking="high",
    timeout_seconds=2400,
    workers={"programmer": {"thinking": "low"}},
)


class ConfigureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)
        self.path = self.root / ".concorde/config.json"

    def document(self) -> dict:
        return json.loads(self.path.read_text())

    def request(self, data: dict, mode: str = "execute") -> dict:
        return run_operation(
            "concorde-configure",
            CONFIGURATION,
            typed("concorde-configure-request", data),
            host_context=OperationHost(
                self.root, PACKAGE, mode=mode, allow_primary_worktree=True
            ),
        )

    @verifies("scenario.admission.configure-propose")
    def test_propose_returns_a_digest_bound_proposal_and_changes_nothing(self):
        before = self.path.read_bytes()
        response = configure.propose(self.root, PACKAGE, SELECTION)["data"]
        self.assertEqual("proposed", response["status"])
        proposal = response["proposal"]
        self.assertEqual(
            {
                "path": ".concorde/config.json",
                "source_digest": digest_bytes(before),
                "configuration": SELECTION,
                "protocol": None,
            },
            proposal["data"],
        )
        self.assertEqual(digest_bytes(proposal), response["proposal_digest"])
        self.assertEqual(CONFIGURATION, response["configuration"])
        self.assertEqual(before, self.path.read_bytes())
        unchanged = configure.propose(self.root, PACKAGE, CONFIGURATION)["data"]
        self.assertEqual(
            ("unchanged", None, None),
            (
                unchanged["status"],
                unchanged["proposal"],
                unchanged["proposal_digest"],
            ),
        )

    @verifies("scenario.admission.configure-apply")
    def test_apply_writes_exactly_the_reviewed_proposal(self):
        original = self.document()
        result = self.request({"action": "propose", "configuration": SELECTION})
        self.assertEqual("succeeded", result["status"], result)
        proposed = result["output"]["data"]
        result = self.request(
            {
                "action": "apply",
                "proposal": proposed["proposal"],
                "proposal_digest": proposed["proposal_digest"],
            }
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("applied", result["output"]["data"]["status"])
        self.assertEqual(SELECTION, load_configuration(self.root))
        stored = self.document()
        self.assertEqual({**original, "operation_configuration": SELECTION}, stored)
        SpecRepository(self.root, PACKAGE)

    @verifies("scenario.admission.configure-stale")
    def test_a_changed_configuration_file_refuses_the_proposal(self):
        proposed = configure.propose(self.root, PACKAGE, SELECTION)["data"]
        self.path.write_text(json.dumps({**self.document(), "note": True}, indent=2))
        before = self.path.read_bytes()
        with self.assertRaises(SpecError) as raised:
            configure.apply(
                self.root,
                PACKAGE,
                proposed["proposal"],
                proposed["proposal_digest"],
            )
        self.assertEqual("stale_proposal", raised.exception.code)
        self.assertEqual(before, self.path.read_bytes())

    @verifies("scenario.admission.configure-altered-proposal")
    def test_an_altered_proposal_is_refused(self):
        proposed = configure.propose(self.root, PACKAGE, SELECTION)["data"]
        altered = copy.deepcopy(proposed["proposal"])
        altered["data"]["configuration"] = configuration(thinking="low")
        before = self.path.read_bytes()
        with self.assertRaises(SpecError) as raised:
            configure.apply(self.root, PACKAGE, altered, proposed["proposal_digest"])
        self.assertEqual("invalid_proposal", raised.exception.code)
        self.assertEqual(before, self.path.read_bytes())

    @verifies("scenario.admission.configure-invalid")
    def test_an_invalid_configuration_leaves_the_file_unchanged(self):
        before = self.path.read_bytes()
        self.assertEqual({}, validate_typed(configuration())["data"])
        for data in (
            {"integration": "codex", "enforcement": "native"},
            {"reasoning_effort": "high"},
            {"thinking": "ultra"},
            {"workers": {"programmer": {"integration": "claude"}}},
        ):
            with self.subTest(data=data):
                with self.assertRaises(TypedDataError) as raised:
                    configure.propose(self.root, PACKAGE, configuration(**data))
                self.assertTrue(raised.exception.field, raised.exception)
                self.assertEqual(before, self.path.read_bytes())
        proposed = configure.propose(self.root, PACKAGE, SELECTION)["data"]
        forged = copy.deepcopy(proposed["proposal"])
        forged["data"]["configuration"] = configuration(thinking="ultra")
        with self.assertRaises(TypedDataError):
            configure.apply(
                self.root, PACKAGE, forged, configure.proposal_digest(forged)
            )
        self.assertEqual(before, self.path.read_bytes())
        # A write after which the project no longer loads is restored.
        with (
            patch.object(
                configure, "SpecRepository", side_effect=SpecError("does not load")
            ),
            self.assertRaises(SpecError),
        ):
            configure.apply(
                self.root,
                PACKAGE,
                proposed["proposal"],
                proposed["proposal_digest"],
            )
        self.assertEqual(before, self.path.read_bytes())

    @verifies("scenario.admission.configure-preview-refused")
    def test_describe_policy_is_refused(self):
        result = self.request(
            {"action": "propose", "configuration": SELECTION}, mode="describe-policy"
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("use_proposal", result["errors"][0]["code"])


class AcceptProtocolTests(unittest.TestCase):
    """The binding moves to the installer's Protocol copy only on explicit acceptance."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)

    def configure(self, data: dict) -> dict:
        return run_operation(
            "concorde-configure",
            CONFIGURATION,
            typed("concorde-configure-request", data),
            host_context=OperationHost(self.root, PACKAGE, allow_primary_worktree=True),
        )

    @verifies(
        "scenario.admission.accept-protocol",
        "scenario.admission.protocol-not-accepted",
    )
    def test_configure_accepts_an_upgraded_protocol_only_on_explicit_request(self):
        # An installation update refreshed the copy under .concorde/protocol/ while the project's
        # binding still names the previously accepted manifest.
        manifest = self.root / PROTOCOL_MANIFEST_PATH
        installed = manifest.read_bytes()
        config = self.root / ".concorde/config.json"
        value = json.loads(config.read_text())
        previous = {
            "version": value["protocol"]["version"],
            "digest": "sha256:" + "0" * 64,
        }
        value["protocol"] = previous
        config.write_text(json.dumps(value))
        with self.assertRaises(SpecError) as raised:
            SpecRepository(self.root, PACKAGE)
        self.assertEqual("protocol_mismatch", raised.exception.code)
        result = self.configure({"action": "propose", "configuration": CONFIGURATION})
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("protocol_mismatch", result["errors"][0]["code"])
        self.assertEqual(previous, json.loads(config.read_text())["protocol"])
        result = self.configure(
            {
                "action": "propose",
                "configuration": CONFIGURATION,
                "accept_protocol": True,
            }
        )
        self.assertEqual("succeeded", result["status"], result)
        proposed = result["output"]["data"]
        self.assertEqual("proposed", proposed["status"])
        self.assertEqual(previous, json.loads(config.read_text())["protocol"])
        result = self.configure(
            {
                "action": "apply",
                "proposal": proposed["proposal"],
                "proposal_digest": proposed["proposal_digest"],
            }
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(
            {"version": previous["version"], "digest": digest_bytes(installed)},
            json.loads(config.read_text())["protocol"],
        )
        self.assertEqual(
            protocol_binding(PACKAGE), json.loads(config.read_text())["protocol"]
        )
        # Acceptance rebinds; it never writes the installer-owned copy.
        self.assertEqual(installed, manifest.read_bytes())
        for path, content in protocol_files(PACKAGE).items():
            self.assertEqual(content, (self.root / path).read_bytes())
        SpecRepository(self.root, PACKAGE)


if __name__ == "__main__":
    unittest.main()
