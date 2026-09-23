"""Dispatch of an admitted request to the entry point its declaration names, and child requests.

Dispatch imports no provider: it reads the declaration and calls the entry point it names. A Host
service's entry point runs to its end; an Agent call and a pi workflow go, with the Agent the
declaration names or the workflow hook its entry point names, to the native driver the Pi session
supplied. Target, workspace and configuration checks happen in admission before dispatch, stage
rules in the provider after it.
"""

from __future__ import annotations

from dataclasses import replace

from ..harness.admission import resolve_entry
from ..harness.admission import run_operation as admit
from ..harness.host import (
    AdmissionServices,
    AdmittedRequest,
    InstallationService,
    OperationHost,
)
from ..spec.repository import SpecError
from .catalog import CATALOG, declarations


def _native_required(request: AdmittedRequest) -> SpecError:
    return SpecError(
        f"{request.operation} runs only through the native preparation the Pi session supplies",
        "native_required",
    )


def dispatch(request: AdmittedRequest) -> dict:
    """Run one admitted request by its declared kind; return the capability's response."""
    operation = CATALOG[request.operation]
    entry = operation.declaration["entry_point"]
    if operation.kind == "host":
        return resolve_entry(entry)(request)
    driver = request.host.native_driver
    if operation.kind == "agent-call":
        if driver is None:
            raise _native_required(request)
        return driver.agent_call(request, operation.agents[0][0])
    if driver is None:
        # A workflow hook may serve a request that needs no Workflow in place.
        serve = getattr(
            resolve_entry(entry, callable_required=False), "serve_in_place", None
        )
        served = serve(request) if serve is not None else None
        if served is None:
            raise _native_required(request)
        return served
    return driver.workflow(request, entry)


def services(installation: InstallationService | None = None) -> AdmissionServices:
    """The declarations and the dispatcher admission receives, with an installation service."""
    return AdmissionServices(
        catalog=declarations(), dispatcher=dispatch, installation=installation
    )


def run_child(
    parent: str, child: str, configuration: dict, payload: dict, host: OperationHost
) -> dict:
    """Run ``child`` for a running ``parent`` as a new capability request; return its envelope.

    The child must be a cataloged public Operation that the parent's declaration lists in
    ``USES``; it is admitted, dispatched and recorded exactly like a direct request, with the
    parent's configuration and workspace.
    """
    for name in (parent, child):
        if name not in CATALOG or not CATALOG[name].public:
            raise SpecError(f"unknown operation: {name}", "unknown_operation")
    if child not in CATALOG[parent].uses:
        raise SpecError(
            f"{parent} has no declared composition edge to {child}",
            "undeclared_operation",
        )
    return run_operation(child, configuration, payload, host_context=host)


def run_operation(
    operation: str,
    configuration: dict | None,
    runtime_input: dict,
    *,
    host_context: OperationHost,
) -> dict:
    """Admit one request in this process with this catalog, as an embedding program does."""
    if host_context.services is None:
        host_context = replace(host_context, services=services())
    return admit(operation, configuration, runtime_input, host_context=host_context)
