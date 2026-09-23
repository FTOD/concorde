"""A prepared native Domain Agent gets its profile's tools, `report_issue` and nothing inherited."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.native_context import execute
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.harness.worker_profile import worker_profile
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import PACKAGE, project

DOMAIN_AGENTS = (
    "context_assessor",
    "planner",
    "task_author",
    "programmer",
    "spec_reviewer",
    "code_reviewer",
    "issue_solver",
)
PREPARED = {
    "concorde-context-solve": "context_assessor",
    "concorde-spec-review": "spec_reviewer",
    "concorde-code-review": "code_reviewer",
}
DELEGATION = {"subagent", "concorde"}


def front_matter(path: Path) -> dict:
    _, header, _ = path.read_text().split("---", 2)
    return dict(line.split(": ", 1) for line in header.strip().splitlines())


class DomainToolTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(self.root)
        runtime = patch(
            "concorde.harness.native_context.admit_native_runtime",
            return_value=NativeRuntimeBinding(
                FORMAT, str(self.root), "sha256:" + "0" * 64
            ),
        )
        runtime.start()
        self.addCleanup(runtime.stop)

    def prepare(self, operation: str) -> dict:
        envelope = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": operation,
            "mode": "execute",
            "configuration": None,
            "input": typed(
                operation + "-request",
                {"target_id": "service.transfer", "task": "Assess transfer"},
            ),
        }
        prepared = execute(
            PACKAGE,
            "prepare",
            {
                "invocation": envelope,
                "native_root": str(self.root),
                "session_id": "unit",
            },
        )
        self.assertEqual("prepared", prepared["state"], prepared)
        self.addCleanup(
            shutil.rmtree, Path(prepared["call"]["cwd"]).parent, ignore_errors=True
        )
        return prepared

    @verifies("scenario.agents.domain-tools")
    def test_only_the_programmer_profile_may_change_files(self):
        for name in DOMAIN_AGENTS:
            with self.subTest(agent=name):
                tools = set(worker_profile(name).tools)
                self.assertFalse(tools & DELEGATION)
                self.assertEqual(
                    name == "programmer", bool(tools & {"edit", "write"}), tools
                )
                self.assertEqual(
                    name in {"programmer", "code_reviewer"}, "bash" in tools, tools
                )

    @verifies("scenario.agents.domain-tools")
    def test_prepared_agent_has_its_tools_and_fresh_uninherited_context(self):
        for operation, name in PREPARED.items():
            with self.subTest(operation=operation):
                prepared = self.prepare(operation)
                call = prepared["call"]
                self.assertEqual("fresh", call["context"])
                definition = front_matter(
                    Path(call["cwd"]) / ".pi/agents" / (call["agent"] + ".md")
                )
                expected = [
                    tool
                    for tool in worker_profile(name).tools
                    if not (name == "code_reviewer" and tool == "bash")
                ] + ["report_issue"]
                tools = definition["tools"].split(", ")
                self.assertEqual(expected, tools)
                self.assertFalse(set(tools) & (DELEGATION | {"edit", "write", "bash"}))
                for key in (
                    "inheritProjectContext",
                    "inheritGlobalContext",
                    "inheritSkills",
                    "allowNestedSubagents",
                ):
                    self.assertFalse(json.loads(definition[key]), key)
                self.assertEqual('"fresh"', definition["defaultContext"])
                self.assertEqual('"replace"', definition["systemPromptMode"])


if __name__ == "__main__":
    unittest.main()
