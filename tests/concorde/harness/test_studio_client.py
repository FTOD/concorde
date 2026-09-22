"""Transport failures must never duplicate a operation invocation or contaminate JSON stdout."""

import contextlib
import importlib
import io
import json
import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock, patch
from urllib.error import URLError
from uuid import uuid4

from concorde.harness.entry import json_main
from concorde.harness.studio_client import _NoRedirect, run_in_studio
from concorde.spec.contracts import load_operation_inventory
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.harness.test_studio import invocation
from tests.concorde.spec.support import PACKAGE
from tests.concorde.support.environment import scrubbed_process_environment


class StudioClientTests(unittest.TestCase):
    def setUp(self):
        self.thread, self.run_id = str(uuid4()), str(uuid4())
        self.value = invocation()
        self.result = {
            "type_id": "concorde-operation-result",
            "schema_version": 3,
            "operation_id": self.value["operation_id"],
            "mode": "execute",
            "status": "succeeded",
            "invocation_id": str(uuid4()),
            "workspace": None,
            "output": {},
            "errors": [],
        }

    def opener(self, responses):
        calls = []

        def open_request(request, **kwargs):
            calls.append(request)
            value = next(responses)
            if isinstance(value, Exception):
                raise value
            response = Mock()
            response.__enter__ = Mock(
                return_value=io.BytesIO(json.dumps(value).encode())
            )
            response.__exit__ = Mock(return_value=False)
            return response

        return Mock(open=open_request), calls

    def test_remote_and_redirect_urls_are_rejected(self):
        for url in [
            "https://localhost:2024",
            "http://example.com",
            "http://localhost/path",
            "http://user@localhost",
            "http://localhost?x=1",
            "http://localhost#other",
        ]:
            with (
                self.subTest(url=url),
                patch("concorde.harness.studio_client.build_opener") as factory,
            ):
                with self.assertRaises(SpecError):
                    run_in_studio(url, self.value, Path.cwd(), PACKAGE)
                factory.assert_not_called()
        self.assertIsNone(
            cast(Any, _NoRedirect()).redirect_request(
                None, None, 302, "", {}, "http://other"
            )
        )

    def test_connection_loss_after_submission_never_retries_or_runs_locally(self):
        opener, calls = self.opener(
            iter(
                [
                    {"thread_id": self.thread},
                    URLError("response lost after accepting run"),
                ]
            )
        )
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch("concorde.harness.studio_client.build_opener", return_value=opener),
            patch("concorde.harness.admission.run_operation") as local,
            scrubbed_process_environment(CONCORDE_STUDIO_URL="http://127.0.0.1:2024"),
            patch("sys.stdin", io.StringIO(json.dumps(self.value))),
            patch("sys.argv", ["run-operation.py"]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            inventory = load_operation_inventory()
            module = importlib.import_module(f"{inventory.__name__}.issues")
            code = json_main(PACKAGE, "concorde-issues", runner=module.run)
        local.assert_not_called()
        self.assertEqual([], calls)
        self.assertEqual(3, code)
        result = json.loads(stdout.getvalue())
        self.assertEqual("native_required", result["errors"][0]["code"])

    def test_polling_and_policies_preserve_the_server_result(self):
        state = {"result": self.result, "policies": [{"phase": "ask"}], "events": []}
        opener, calls = self.opener(
            iter(
                [
                    {"thread_id": self.thread},
                    {"run_id": self.run_id, "status": "pending"},
                    {"run_id": self.run_id, "status": "running"},
                    {"run_id": self.run_id, "status": "success"},
                    {"values": state},
                ]
            )
        )
        with (
            patch(
                "concorde.harness.studio_client.build_opener", return_value=opener
            ) as factory,
            patch("concorde.harness.studio_client.time.sleep"),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            actual = run_in_studio(
                "http://localhost:2024", self.value, Path.cwd(), PACKAGE
            )
        self.assertEqual(state, actual)
        self.assertEqual({}, factory.call_args.args[0].proxies)
        payload = json.loads(calls[1].data)
        self.assertEqual(self.value, payload["input"]["invocation"])
        self.assertEqual(
            str(Path.cwd()), payload["input"]["expected_workspace"]["project_root"]
        )
        self.assertEqual(2, sum(call.data is not None for call in calls))

    def test_failed_and_interrupted_runs_report_thread_without_reading_stale_state(
        self,
    ):
        for status in ["error", "interrupted", "timeout"]:
            opener, calls = self.opener(
                iter(
                    [
                        {"thread_id": self.thread},
                        {"run_id": self.run_id, "status": status},
                    ]
                )
            )
            with (
                self.subTest(status=status),
                patch(
                    "concorde.harness.studio_client.build_opener", return_value=opener
                ),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SpecError) as error:
                    run_in_studio(
                        "http://localhost:2024", self.value, Path.cwd(), PACKAGE
                    )
                self.assertEqual("studio_run_failed", error.exception.code)
                self.assertIn(self.thread, str(error.exception))
                self.assertEqual(2, len(calls))

    def test_incompatible_result_is_rejected(self):
        for changes in [
            {"mode": "describe-policy"},
            {"operation_id": "concorde-plan"},
            {"status": "success"},
            {"schema_version": True},
            {"errors": "bad"},
        ]:
            opener, _ = self.opener(
                iter(
                    [
                        {"thread_id": self.thread},
                        {"run_id": self.run_id, "status": "success"},
                        {"values": {"result": {**self.result, **changes}}},
                    ]
                )
            )
            with (
                self.subTest(changes=changes),
                patch(
                    "concorde.harness.studio_client.build_opener", return_value=opener
                ),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SpecError) as error:
                    run_in_studio(
                        "http://localhost:2024", self.value, Path.cwd(), PACKAGE
                    )
                self.assertEqual("incompatible_handoff", error.exception.code)

    @verifies("scenario.harness.graph-inspection")
    def test_documented_optional_operation_is_the_real_inspectable_graph(self):
        from concorde.harness.studio import build_studio_graph

        guide = (PACKAGE / "scripts/development/STUDIO.md").read_text()
        self.assertIn('OperationNode("context_assessor").graph()', guide)
        self.assertIn("terminal-agent-operation", guide)
        graph = build_studio_graph()
        self.assertEqual(
            set(graph.get_graph().nodes), {"__start__", "terminal_agent", "__end__"}
        )
