"""``concorde-configure``: a digest-bound proposal and apply of the stored operation configuration.

``propose`` changes nothing: it returns a ``concorde-configuration-proposal`` bound to the digest of
the configuration file it was computed from, and the digest of the proposal itself. ``apply`` writes
exactly the proposal whose digest it names, and only while the file still has the proposal's source
digest, through a file transaction kept only if the project then loads.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..spec.changes import apply_files
from ..spec.initialize import installed_protocol_binding
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import (
    DIGEST,
    STRING,
    decode,
    obj,
    register,
    typed,
    typed_schema,
)
from .configuration import CONFIG_PATH, CONFIG_TYPE, admit_configuration

PROPOSAL_TYPE = "concorde-configuration-proposal"
PROPOSAL = obj(
    {
        "path": {"const": CONFIG_PATH},
        "source_digest": DIGEST,
        "configuration": typed_schema(CONFIG_TYPE),
        "protocol": {
            "anyOf": [obj({"version": STRING, "digest": DIGEST}), {"type": "null"}]
        },
    }
)
register(PROPOSAL_TYPE, 1, PROPOSAL)

# The request and response of the capability; the declaration in ``operations/configure.py`` names
# them and the catalog registers them.
REQUEST = obj(
    {
        "action": {"enum": ["propose", "apply"]},
        "configuration": typed_schema(CONFIG_TYPE),
        "accept_protocol": {"type": "boolean"},
        "proposal": typed_schema(PROPOSAL_TYPE),
        "proposal_digest": DIGEST,
        "run_in_primary": {"type": "boolean"},
    },
    (
        "configuration",
        "accept_protocol",
        "proposal",
        "proposal_digest",
        "run_in_primary",
    ),
)
REQUEST_VERSION = 4
RESPONSE = obj(
    {
        "status": {"enum": ["proposed", "unchanged", "applied"]},
        "proposal": {"anyOf": [typed_schema(PROPOSAL_TYPE), {"type": "null"}]},
        "proposal_digest": {"anyOf": [DIGEST, {"type": "null"}]},
        "configuration": typed_schema(CONFIG_TYPE),
    }
)
RESPONSE_VERSION = 3


def proposal_digest(proposal: dict) -> str:
    """The ``sha256:`` digest of the canonical JSON of a proposal typed value."""
    return digest(proposal)


def _document(project: Path) -> tuple[bytes, dict]:
    source = read_file(project, CONFIG_PATH)
    document = decode(source.decode("utf-8"))
    if not isinstance(document, dict):
        raise SpecError("project configuration must be a JSON object", "invalid_input")
    return source, document


def _response(status: str, configuration, proposal=None) -> dict:
    return typed(
        "concorde-configure-response",
        {
            "status": status,
            "proposal": proposal,
            "proposal_digest": proposal_digest(proposal) if proposal else None,
            "configuration": configuration,
        },
    )


def propose(
    project_root: Path,
    package_root: Path,
    configuration: dict,
    accept_protocol: bool = False,
) -> dict:
    """The configure response for a proposal of ``configuration``; writes nothing."""
    project = Path(project_root)
    configuration = admit_configuration(configuration)
    source, document = _document(project)
    protocol = None
    if accept_protocol:
        installed = installed_protocol_binding(project)
        if document.get("protocol") != installed:
            protocol = installed
    else:
        # Loading refuses a Protocol binding that does not match the installed copy.
        SpecRepository(project, package_root)
    stored = document.get("operation_configuration")
    if stored == configuration and protocol is None:
        return _response("unchanged", stored)
    proposal = typed(
        PROPOSAL_TYPE,
        {
            "path": CONFIG_PATH,
            "source_digest": digest(source),
            "configuration": configuration,
            "protocol": protocol,
        },
    )
    return _response("proposed", stored, proposal)


def apply(
    project_root: Path, package_root: Path, proposal: dict, named_digest: str
) -> dict:
    """Write exactly the proposal ``named_digest`` identifies, if its source is unchanged."""
    project = Path(project_root)
    if proposal_digest(proposal) != named_digest:
        raise SpecError(
            "proposal_digest is not the digest of the given proposal",
            "invalid_proposal",
        )
    data = proposal["data"]
    configuration = admit_configuration(
        data["configuration"], "/proposal/data/configuration"
    )
    source, document = _document(project)
    if digest(source) != data["source_digest"]:
        raise SpecError(
            "the configuration file changed since the proposal; propose again",
            "stale_proposal",
        )
    if (
        data["protocol"] is not None
        and installed_protocol_binding(project) != data["protocol"]
    ):
        raise SpecError(
            "the installed Protocol copy changed since the proposal; propose again",
            "stale_proposal",
        )
    document["operation_configuration"] = configuration
    if data["protocol"] is not None:
        document["protocol"] = data["protocol"]
    apply_files(
        project,
        [
            {
                "path": CONFIG_PATH,
                "before_digest": data["source_digest"],
                "content": json.dumps(document, indent=2) + "\n",
            }
        ],
        {CONFIG_PATH},
        verify=lambda: SpecRepository(project, package_root),
    )
    return _response("applied", configuration)


def run(request) -> dict:
    """Entry point of ``concorde-configure``."""
    host, data = request.host, request.data
    if host.mode == "describe-policy":
        raise SpecError(
            "the configuration proposal is the preview of concorde-configure",
            "use_proposal",
        )
    if data["action"] == "propose":
        if "configuration" not in data:
            raise SpecError(
                "propose requires configuration", "invalid_input", "/configuration"
            )
        return propose(
            host.project_root,
            host.package_root,
            data["configuration"],
            bool(data.get("accept_protocol")),
        )
    if not {"proposal", "proposal_digest"} <= set(data):
        raise SpecError(
            "apply requires proposal and proposal_digest", "invalid_input", "/proposal"
        )
    return apply(
        host.project_root, host.package_root, data["proposal"], data["proposal_digest"]
    )
