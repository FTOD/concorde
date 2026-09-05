"""Explicit process doubles for JSON Operation integration tests.

Only the external model process is substituted. The real graph, launch policy,
completion decoder, receipt checks, artifact IO, and delivery tools still run.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from concorde.capabilities.operation_data import typed
from concorde.capabilities.operation_executor import AgentProcessExecutor


CONFIGURATION = typed("concorde-operation-configuration", {"integration": "claude", "enforcement": "native"})


def invocation(operation: str, data: dict, *, configuration: dict | None = None,
               mode: str = "describe-policy") -> dict:
    from concorde.capabilities.operation_data import OPERATION_CONTRACTS

    return {"type_id": "concorde-operation-invocation", "schema_version": 1,
            "operation_id": operation, "mode": mode,
            "configuration": configuration or CONFIGURATION,
            "input": typed(OPERATION_CONTRACTS[operation][0], data)}


def configure(project: Path, configuration: dict | None = None) -> dict:
    value = configuration or CONFIGURATION
    path = project / ".concorde/config.json"
    document = json.loads(path.read_text())
    document["operation_configuration"] = value
    path.write_text(json.dumps(document) + "\n")
    return value


def investigation_result(runtime_input: dict) -> dict:
    data = runtime_input["data"]
    task = data["task"]["data"]
    return typed("concorde-reflection-investigation-result", {"findings": [
        {"reflection_id": identifier, "verified_commit": data["head"], "observed_state": "reproduced",
         "verification": "The process double reproduced the fixture behavior at the supplied HEAD.",
         "analysis": "The fixture behavior differs from its declared feature contract.",
         "resolution": "Apply the bounded fixture change and its verification.",
         "intervention_rationale": "The explicit fixture task provides the required scope and authority.",
         "human_intervention": "not-required", "route": task.get("route", "plan"),
         "effort": "small", "files": [data["feature_path"]],
         "steps": "Implement the selected fixture change.", "validation": "Run the fixture contract checks.",
         "risks": "Preserve all unrelated fixture behavior.", "protocol_change": False}
        for identifier in task["reflection_ids"]]})


class ScriptedAgent:
    def __init__(self, callback=None, failure: str | None = None):
        self.callback = callback
        self.failure = failure
        self.calls: list[dict] = []
        self.executor = AgentProcessExecutor(runner=self.run,
                                            version_probe=lambda *args: "claude-code 4.2")

    def run(self, argv, *, cwd, env, input_text):
        schema = json.loads(argv[argv.index("--json-schema") + 1])
        properties = schema["properties"]
        capability = properties["capability"]["const"]
        runtime_input = json.JSONDecoder().raw_decode(input_text.split("Typed runtime input (consume only these contracted fields):\n", 1)[1])[0]
        configuration = json.JSONDecoder().raw_decode(input_text.split("Operation configuration (project snapshot):\n", 1)[1])[0]
        assert "Prior results:" not in input_text
        self.calls.append({"capability": capability, "input": runtime_input, "configuration": configuration})
        failed = capability == self.failure
        domain_output = None
        if self.callback is not None and not failed:
            domain_output = self.callback(capability, runtime_input, Path(cwd))
        if capability == "concorde-analyze" and not failed and domain_output is None:
            domain_output = investigation_result(runtime_input)
        payload = {key: item["const"] for key, item in properties.items() if "const" in item}
        payload.update(status="failed" if failed else "success", output="fixture audit summary only",
                       limitations="injected failure" if failed else "none",
                       gates=[{"name": "fixture-task", "status": "failed" if failed else "passed",
                               "evidence": "explicit model-process double; host verifies artifacts and receipts"}])
        if "domain_output" in properties:
            payload["domain_output"] = domain_output
        return subprocess.CompletedProcess(argv, 0, json.dumps({"structured_output": payload}), "")
