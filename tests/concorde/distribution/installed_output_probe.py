"""Run only as an OS-read-only tester command; retain bounded output provenance."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

source = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(source / "src"), str(source)]
from tests.concorde.support.install_output_handoff import (  # noqa: E402
    install_selected_fixture,
)

scratch = Path(os.environ["CONCORDE_CHECK_TMPDIR"])
# Wheel input is preexisting host /tmp data, read through the tester's explicit read-only view.
wheels = Path(os.environ["PIP_FIND_LINKS"])
if wheels.is_relative_to("/tmp"):
    os.environ["PIP_FIND_LINKS"] = str(
        Path(os.environ["CONCORDE_TEST_HOST_TMP"]) / wheels.relative_to("/tmp")
    )
selection = Path(os.environ["CONCORDE_SESSION_SELECTION"])
original = selection.read_bytes()
try:
    (source / "README.md").open("a").close()
except OSError as error:
    assert error.errno == 30
else:
    raise AssertionError("governing tree is not read-only")
record, environment = install_selected_fixture(scratch / "consumer", selection)
assert selection.read_bytes() == original and os.environ[
    "CONCORDE_SESSION_SELECTION"
] == str(selection)
installed = record["installed"]
# The existing strict source-private boundary must STILL refuse use against installed code.
refused = subprocess.run(
    [installed["python"], installed["runtime"], "concorde-issues", "--runtime-check"],
    cwd=record["destination"],
    env=dict(environment, CONCORDE_SESSION_SELECTION=str(selection)),
    capture_output=True,
    text=True,
    check=False,
)
assert refused.returncode == 3
assert json.loads(refused.stdout)["errors"][0]["code"] == "invalid_build", (
    refused.stdout
)
smoke = subprocess.run(
    [
        "node",
        str(source / "tests/concorde/harness/native_context_probe.mjs"),
        sys.argv[1],
        sys.argv[2],
        installed["framework"],
        "sufficient",
    ],
    cwd=record["destination"],
    env={
        **environment,
        "CONCORDE_NATIVE_PROBE_PROJECT": record["destination"],
        "CONCORDE_NATIVE_PROBE_PYTHON": installed["python"],
        "CONCORDE_NATIVE_FIXTURE_SOURCE": str(source),
    },
    capture_output=True,
    text=True,
    timeout=150,
    check=False,
)
assert smoke.returncode == 0, smoke.stderr[-4000:]
value = json.loads(smoke.stdout.strip().splitlines()[-1])
assert value["accepted"] and value["realModelCalls"] == 0
summary = {
    "provenance": record,
    "native": value,
    "source_readonly": True,
    "source_selection_unchanged": True,
    "inherited_selection_refused": True,
    "provenance_sha256": hashlib.sha256(
        (scratch / "installed-output-provenance.json").read_bytes()
    ).hexdigest(),
}
text = json.dumps(summary)
assert len(text.encode()) < 8000
print(text)
