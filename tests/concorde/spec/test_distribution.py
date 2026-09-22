"""Installed source closure and the Pi completion adapter, with explicit process doubles."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.distribution.build import load_model_instructions
from concorde.distribution.package_validation import validate_package
from concorde.spec.contracts import MODEL_OPERATIONS, OPERATION_NAMES, contracts
from concorde.spec.repository import SpecRepository
from concorde.spec.typed_data import typed
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.managed_runtime import independent_runtime_environment

from .support import CONFIGURATION, PACKAGE, ModelProcessDouble, project


class DistributionTests(unittest.TestCase):
    def test_catalog_roles_and_exported_schemas_are_executable_package_contracts(self):
        self.assertEqual([], validate_package(PACKAGE))
        self.assertEqual(18, len(OPERATION_NAMES))
        self.assertEqual(7, len(MODEL_OPERATIONS))
        self.assertIn("concorde-context-solve", OPERATION_NAMES)
        self.assertNotIn("concorde-ask", OPERATION_NAMES)
        self.assertIn("concorde-planner", MODEL_OPERATIONS)
        self.assertNotIn("concorde-main", MODEL_OPERATIONS)
        for role in MODEL_OPERATIONS:
            prompt = load_model_instructions(PACKAGE, role)
            self.assertEqual(role, prompt.name)
            self.assertTrue(prompt.body.strip())
            self.assertIsNotNone(prompt.effects)

    @verifies(
        "scenario.spec.admit-inventory",
        "scenario.spec.shared-file",
        "scenario.spec.validate-success",
    )
    def test_self_architecture_lists_every_implementation_file_under_an_entity(self):
        repo = SpecRepository(PACKAGE)
        report = validate_repository(PACKAGE)
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertEqual("module.concorde", repo.select("module.agents").parent)
        self.assertEqual("module.concorde", repo.select("module.operations").parent)
        self.assertTrue(all(t.kind == "module" for t in repo.targets.values()))
        self.assertEqual("module.concorde", repo.select("module.views").parent)
        self.assertIn(
            "src/concorde/views",
            repo.implementation_paths(repo.select("module.views")),
        )
        for target in repo.targets.values():
            self.assertEqual(
                list(target.files), sorted(repo.realization_entries(target))
            )
        shared = [path for path, users in repo.file_users.items() if len(users) > 1]
        self.assertTrue(
            shared,
            "the self-hosted project shares implementation files between Modules",
        )
        for path in shared:
            self.assertEqual(
                set(repo.listing_users(path)),
                {t.id for t in repo.affected_modules([path])},
            )
        self.assertTrue(
            {"module.planning", "module.review"}
            <= {
                t.id
                for t in repo.affected_modules(
                    ["tests/concorde/operations/test_specify_loop.py"]
                )
            }
        )
        text = "\n".join(
            repo.source_bytes(path).decode()
            for path in repo.spec_files("module.harness")
        )
        for op in contracts():
            self.assertIn(op + "-request", text)

    def test_launcher_refuses_a_nonpublic_operation_name_and_accepts_a_public_operation(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            launcher = str(PACKAGE / "scripts/run-operation.py")
            internal_command = [sys.executable, launcher, "concorde-planner"]
            internal_value = {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": "concorde-planner",
                "mode": "execute",
                "configuration": None,
                "input": typed(
                    "concorde-plan-request",
                    {"target_id": "service.transfer", "task": "Explain transfer"},
                ),
            }
            result = subprocess.run(
                internal_command,
                input=json.dumps(internal_value),
                capture_output=True,
                text=True,
                cwd=root,
            )
            self.assertEqual(3, result.returncode, result.stdout + result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual("blocked", output["status"])
            self.assertEqual("unknown_operation", output["errors"][0]["code"])
            public_command = [sys.executable, launcher, "concorde-validate"]
            public_value = {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": "concorde-validate",
                "mode": "describe-policy",
                "configuration": None,
                "input": typed(
                    "concorde-validate-request",
                    {"target_id": "service.transfer", "task": "Explain transfer"},
                ),
            }
            result = subprocess.run(
                public_command,
                input=json.dumps(public_value),
                capture_output=True,
                text=True,
                cwd=root,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("described", json.loads(result.stdout)["status"])
            result = subprocess.run(
                public_command + ["--feature-path", "specs/transfer/module.md"],
                input=json.dumps(public_value),
                capture_output=True,
                text=True,
                cwd=root,
            )
            self.assertEqual(3, result.returncode)
            self.assertEqual("blocked", json.loads(result.stdout)["status"])

    def test_installed_framework_runs_complete_real_graph_and_checks_for_pi(
        self,
    ):
        # Exercise the supported bootstrap and local admission, not hand-copied outputs
        # or a receipt/dependency double. Only model execution is replaced below.
        for integration in ("pi",):
            with (
                self.subTest(integration=integration),
                tempfile.TemporaryDirectory() as directory,
            ):
                scratch = Path(directory)
                root = scratch / "consumer"
                root.mkdir()
                environment = independent_runtime_environment(scratch, PACKAGE)
                installed = subprocess.run(
                    [
                        sys.executable,
                        str(PACKAGE / "scripts/install-concorde.py"),
                        "--target",
                        str(root),
                        "--apply",
                        "--format",
                        "json",
                    ],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                self.assertEqual(
                    0, installed.returncode, installed.stdout + installed.stderr
                )
                local_python = root / ".concorde/.venv/bin/python"
                driver = root / "driver.py"
                driver.write_text("""import importlib.util,json,sys
from pathlib import Path
root=Path.cwd();framework=root/'.concorde/framework';sys.path.insert(0,str(framework/'src'));sys.path.append(str(Path(sys.argv[1]).parents[3]))
spec=importlib.util.spec_from_file_location('model_process_fixture',sys.argv[1]);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
helper.PACKAGE=framework
from concorde.spec.typed_data import typed
helper.project(root)
from concorde.harness.admission import run_operation
from tests.concorde.support.native_planning import OperationHost
import concorde.harness.admission as actual_host
model=helper.ModelProcessDouble();host=OperationHost(root,framework,executor=model.executor,allow_primary_worktree=True)
task={'target_id':'service.transfer','task':'Implement transfer'}
outputs=[]
for operation in ('plan','tasks','implement','spec-review','code-review','validate'):
    result=run_operation('concorde-'+operation,None,typed('concorde-'+operation+'-request',task),host_context=host)
    outputs.append(result)
print(json.dumps({'result':result,'outputs':outputs,'module_source':actual_host.__file__,
  'python_prefix':sys.prefix,'stages':[c['stage'] for c in model.calls]}))
""")
                completed = subprocess.run(
                    [
                        str(local_python),
                        str(driver),
                        str(PACKAGE / "tests/concorde/spec/support.py"),
                        integration,
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    env={**environment, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                value = json.loads(completed.stdout)
                self.assertIn(".concorde/framework/src", value["module_source"])
                self.assertEqual(str(root / ".concorde/.venv"), value["python_prefix"])
                self.assertEqual("succeeded", value["result"]["status"], value)
                self.assertTrue(
                    all(output["status"] == "succeeded" for output in value["outputs"]),
                    value,
                )
                self.assertEqual(
                    [
                        "context-solve",
                        "plan",
                        "tasks",
                        "implementation",
                        # The transfer Module, then Banking, which uses it and reads its Specs.
                        "spec-review",
                        "spec-review",
                        "code-review",
                    ],
                    value["stages"],
                )
                self.assertEqual("ready", value["result"]["output"]["data"]["outcome"])
                self.assertEqual(
                    "passed", value["result"]["output"]["data"]["checks"][0]["status"]
                )

    def test_completion_from_previous_invocation_cannot_be_replayed(self):
        from concorde.harness.admission import run_operation
        from tests.concorde.support.native_planning import OperationHost

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            model = ModelProcessDouble()
            saved = []
            replay = [False]

            def executor(launch, *, checks=None, report_issue=None):
                if replay[0]:
                    return saved[0]
                result = model.executor(
                    launch, checks=checks, report_issue=report_issue
                )
                if not saved:
                    saved.append(result)
                return result

            host = OperationHost(
                root, PACKAGE, executor=executor, allow_primary_worktree=True
            )
            task = typed(
                "concorde-context-solve-request",
                {"target_id": "service.transfer", "task": "Explain transfer"},
            )
            first = run_operation(
                "concorde-context-solve", CONFIGURATION, task, host_context=host
            )
            replay[0] = True
            second = run_operation(
                "concorde-context-solve", CONFIGURATION, task, host_context=host
            )
            self.assertEqual("succeeded", first["status"])
            self.assertEqual("blocked", second["status"])
            self.assertEqual("invalid_completion", second["errors"][0]["code"])
