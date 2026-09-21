"""Explicit test-only driver for retained RPC sandbox/relay diagnostics, never a public fallback.

Every provider/module comes from the disposable installed framework. Only the historical domain
composition and entry into this diagnostic driver are injected. Native publication has separate
actual-executor probes; these tests claim local installation and RPC sandbox enforcement only.
"""

import json
import sys
from pathlib import Path

root = Path.cwd()
framework = root / ".concorde/framework"
sys.path.insert(0, str(framework / "src"))
sys.path.append(str(Path(__file__).resolve().parents[3]))
from concorde.harness import relay  # noqa: E402
from concorde.harness.admission import run_operation  # noqa: E402
from concorde.harness.worker_executor import WorkerExecutor  # noqa: E402
from tests.concorde.support.native_planning import OperationHost  # noqa: E402

original = relay.relay_launcher


def diagnostic_launcher(host, candidate, **kwargs):
    admitted = original(host, candidate, **kwargs)
    return [admitted[0], str(Path(__file__).resolve())]


relay.relay_launcher = diagnostic_launcher
value = json.load(sys.stdin)
host = OperationHost(
    root, framework, executor=WorkerExecutor(framework), mode=value["mode"]
)
result = run_operation(
    value["operation_id"], value["configuration"], value["input"], host_context=host
)
print(json.dumps(result))

sys.exit(0 if result["status"] in {"succeeded", "described"} else 3)
