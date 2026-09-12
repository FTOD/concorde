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


if __name__ == "__main__":
    unittest.main()
