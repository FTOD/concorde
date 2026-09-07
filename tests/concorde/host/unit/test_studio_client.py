"""Transport failures must never duplicate a capability invocation or contaminate JSON stdout."""
import contextlib
import importlib
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from uuid import uuid4

from concorde.host.contracts import load_capability_inventory
from concorde.host.capability_host import json_main
from concorde.host.studio_client import run_in_studio, _NoRedirect
from concorde.specification.repository import SpecError
from tests.concorde.host.unit.test_studio import invocation
from tests.concorde.specification.support import PACKAGE


class StudioClientTests(unittest.TestCase):
    def setUp(self):
        self.thread, self.run = str(uuid4()), str(uuid4())
        self.value = invocation()
        self.result = {"type_id": "concorde-operation-result", "schema_version": 2,
            "operation_id": self.value["operation_id"], "mode": "execute", "status": "succeeded",
            "invocation_id": str(uuid4()), "workspace": None, "output": {}, "errors": []}

    def opener(self, responses):
        calls = []
        def open_request(request, **kwargs):
            calls.append(request)
            value = next(responses)
            if isinstance(value, Exception):
                raise value
            response = Mock()
            response.__enter__ = Mock(return_value=io.BytesIO(json.dumps(value).encode()))
            response.__exit__ = Mock(return_value=False)
            return response
        return Mock(open=open_request), calls

    def test_remote_and_redirect_urls_are_rejected(self):
        for url in ["https://localhost:2024", "http://example.com", "http://localhost/path",
                    "http://user@localhost", "http://localhost?x=1", "http://localhost#other"]:
            with self.subTest(url=url), patch("concorde.host.studio_client.build_opener") as factory:
                with self.assertRaises(SpecError):
                    run_in_studio(url, self.value, Path.cwd(), PACKAGE)
                factory.assert_not_called()
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "", {}, "http://other"))

    def test_connection_loss_after_submission_never_retries_or_runs_locally(self):
        opener, calls = self.opener(iter([
            {"thread_id": self.thread}, URLError("response lost after accepting run")]))
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("concorde.host.studio_client.build_opener", return_value=opener), \
             patch("concorde.host.capability_host.run_capability") as local, \
             patch.dict(os.environ, {"CONCORDE_STUDIO_URL": "http://127.0.0.1:2024"}), \
             patch("sys.stdin", io.StringIO(json.dumps(self.value))), patch("sys.argv", ["operation.py"]), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            inventory = load_capability_inventory()
            module = importlib.import_module(f"{inventory.__name__}.reflections_triage")
            code = json_main(PACKAGE, "concorde-reflections-triage", runner=module.run)
        local.assert_not_called()
        self.assertEqual(2, len(calls))
        self.assertEqual(3, code)
        result = json.loads(stdout.getvalue())
        self.assertEqual("studio_transport_failed", result["errors"][0]["code"])
        self.assertIn(self.thread, stderr.getvalue())
        self.assertIn("may still be active", result["errors"][0]["message"])

    def test_polling_and_policies_preserve_the_server_result(self):
        state = {"result": self.result, "policies": [{"phase": "ask"}], "events": []}
        opener, calls = self.opener(iter([{"thread_id": self.thread},
            {"run_id": self.run, "status": "pending"}, {"run_id": self.run, "status": "running"},
            {"run_id": self.run, "status": "success"}, {"values": state}]))
        with patch("concorde.host.studio_client.build_opener", return_value=opener) as factory, \
             patch("concorde.host.studio_client.time.sleep"), contextlib.redirect_stderr(io.StringIO()):
            actual = run_in_studio("http://localhost:2024", self.value, Path.cwd(), PACKAGE)
        self.assertEqual(state, actual)
        self.assertEqual({}, factory.call_args.args[0].proxies)
        payload = json.loads(calls[1].data)
        self.assertEqual(self.value, payload["input"]["invocation"])
        self.assertEqual(str(Path.cwd()), payload["input"]["expected_workspace"]["project_root"])
        self.assertEqual(2, sum(call.data is not None for call in calls))

    def test_failed_and_interrupted_runs_report_thread_without_reading_stale_state(self):
        for status in ["error", "interrupted", "timeout"]:
            opener, calls = self.opener(iter([{"thread_id": self.thread}, {"run_id": self.run, "status": status}]))
            with self.subTest(status=status), patch("concorde.host.studio_client.build_opener", return_value=opener), \
                 contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SpecError) as error:
                    run_in_studio("http://localhost:2024", self.value, Path.cwd(), PACKAGE)
                self.assertEqual("studio_run_failed", error.exception.code)
                self.assertIn(self.thread, str(error.exception))
                self.assertEqual(2, len(calls))

    def test_incompatible_result_is_rejected(self):
        for changes in [{"mode": "describe-policy"}, {"operation_id": "concorde-plan"},
                        {"status": "success"}, {"schema_version": True}, {"errors": "bad"}]:
            opener, _ = self.opener(iter([{"thread_id": self.thread}, {"run_id": self.run, "status": "success"},
                {"values": {"result": {**self.result, **changes}}}]))
            with self.subTest(changes=changes), patch("concorde.host.studio_client.build_opener", return_value=opener), \
                 contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SpecError) as error:
                    run_in_studio("http://localhost:2024", self.value, Path.cwd(), PACKAGE)
                self.assertEqual("incompatible_handoff", error.exception.code)
