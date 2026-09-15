"""concorde-configure admits only the integration and enforcement values the distributed launchers can enforce."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.development.configuration import apply_configuration, load_configuration, propose_configuration  # noqa: E402
from concorde.spec.typed_data import TypedDataError, validate_typed  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402
from tests.concorde.support.capability_json import CONFIGURATION  # noqa: E402
from concorde.development.capability_host import CapabilityHost  # noqa: E402
from concorde.development.capability_service import run_capability  # noqa: E402
from concorde.spec.initialize import protocol_binding  # noqa: E402
from concorde.distribution.project_defaults import PROTOCOL_MANIFEST_PATH, protocol_files  # noqa: E402
from concorde.spec.repository import SpecError, SpecRepository, digest as digest_bytes  # noqa: E402
from concorde.spec.typed_data import typed  # noqa: E402
from tests.concorde.spec.support import PACKAGE, ModelProcessDouble, project  # noqa: E402


def configuration(integration: str = "claude", enforcement: str = "native") -> dict:
    return {"type_id": "concorde-capability-configuration", "schema_version": 1,
            "data": {"integration": integration, "enforcement": enforcement}}


class ConfigureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / ".concorde/config.json"
        self.path.parent.mkdir()
        self.write(CONFIGURATION)

    def write(self, value: dict) -> None:
        self.path.write_text(json.dumps({"profile_version": 12, "registry": ".concorde/specs.json",
                                         "capability_configuration": value}))

    def stored(self) -> dict:
        return json.loads(self.path.read_text())["capability_configuration"]

    @verifies("scenario.distribution.configure-apply")
    def test_supported_configuration_is_applied_atomically(self):
        proposed = propose_configuration(self.root, configuration("codex"))
        self.assertEqual("proposal", proposed.status)
        (self.root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
        self.assertEqual("success", apply_configuration(self.root, "accepted.json").status)
        self.assertEqual(configuration("codex"), self.stored())
        self.assertEqual(configuration("codex"), load_configuration(self.root))
        self.assertEqual("unchanged", apply_configuration(self.root, "accepted.json").status)

    @verifies("scenario.distribution.configure-apply")
    def test_only_native_enforcement_is_admitted(self):
        # The distributed launchers attest no outer sandbox, so ``outer`` is rejected at configuration
        # time rather than accepted and failed at the first Agent launch.
        self.assertEqual("native", validate_typed(configuration())["data"]["enforcement"])
        for enforcement in ("outer", "none", ""):
            with self.subTest(enforcement=enforcement):
                with self.assertRaises(TypedDataError):
                    validate_typed(configuration(enforcement=enforcement))
                self.assertEqual("invalid", propose_configuration(self.root, configuration(enforcement=enforcement)).status)
                self.assertEqual(CONFIGURATION, self.stored())
        proposed = propose_configuration(self.root, configuration("codex"))
        forged = {**proposed.result["proposal"], "configuration": configuration("codex", "outer")}
        (self.root / "forged.json").write_text(json.dumps(forged))
        self.assertEqual("invalid", apply_configuration(self.root, "forged.json").status)
        self.assertEqual(CONFIGURATION, self.stored())
        self.write(configuration(enforcement="outer"))
        with self.assertRaises(TypedDataError):
            load_configuration(self.root)


class AcceptProtocolTests(unittest.TestCase):
    """The binding moves to the installer's Protocol copy under .concorde/protocol/ only on explicit acceptance."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)

    def configure(self, data: dict) -> dict:
        host = CapabilityHost(self.root, PACKAGE, executor=ModelProcessDouble().executor, allow_primary_worktree=True)
        return run_capability("concorde-configure", CONFIGURATION, typed("concorde-configure-request", data), host_context=host)

    @verifies("scenario.distribution.accept-protocol")
    def test_configure_accepts_an_upgraded_protocol_only_on_explicit_request(self):
        # An installation update refreshed the copy under .concorde/protocol/ while the project's
        # binding still names the previously accepted manifest.
        manifest = self.root / PROTOCOL_MANIFEST_PATH
        installed = manifest.read_bytes()
        config = self.root / ".concorde/config.json"
        value = json.loads(config.read_text())
        previous = {"version": value["protocol"]["version"], "digest": "sha256:" + "0" * 64}
        value["protocol"] = previous
        config.write_text(json.dumps(value))
        with self.assertRaises(SpecError) as raised:
            SpecRepository(self.root, PACKAGE)
        self.assertEqual("protocol_mismatch", raised.exception.code)
        result = self.configure({"configuration": CONFIGURATION})
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("protocol_mismatch", result["errors"][0]["code"])
        self.assertEqual(previous, json.loads(config.read_text())["protocol"])
        result = self.configure({"configuration": CONFIGURATION, "accept_protocol": True})
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual({"version": previous["version"], "digest": digest_bytes(installed)},
                         json.loads(config.read_text())["protocol"])
        self.assertEqual(protocol_binding(PACKAGE), json.loads(config.read_text())["protocol"])
        # Acceptance rebinds; it never writes the installer-owned copy.
        self.assertEqual(installed, manifest.read_bytes())
        for path, content in protocol_files(PACKAGE).items():
            self.assertEqual(content, (self.root / path).read_bytes())
        SpecRepository(self.root, PACKAGE)


if __name__ == "__main__":
    unittest.main()
