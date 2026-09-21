"""Deterministic project services, also reusable by explicit Studio Graph adapters."""

from __future__ import annotations

from .changes import apply_files, file_change
from .repository import SpecError, SpecRepository, read_file
from .typed_data import OPERATION_CONTRACTS, canonical, decode, typed


def project_operation(operation, configuration, task, host):
    services = project_nodes(operation, configuration, task, host)
    action = services["select_action"]({})["route"]
    return services[action]({})["output"]


def project_nodes(operation, configuration, task, host):
    END = "__end__"

    from .initialize import apply_project_proposal, project_proposal

    def select_action(state):
        if host.mode == "describe-policy":
            raise SpecError(
                "project proposals are the deterministic preview for this operation",
                "use_proposal",
            )
        return {
            "route": "configure"
            if operation == "concorde-configure"
            else "apply"
            if task["action"] == "apply"
            else "propose"
        }

    def configure(state):
        from .initialize import installed_protocol_binding

        accept = bool(task.get("accept_protocol"))
        if not accept:
            SpecRepository(host.project_root, host.package_root)
        value = decode(read_file(host.project_root, ".concorde/config.json").decode())
        if accept:
            # Explicit acceptance of the Protocol the installer placed under .concorde/protocol/:
            # rebind the configuration to that copy; the repository admission verifies the result
            # before the write is kept.
            value["protocol"] = installed_protocol_binding(host.project_root)
        value["operation_configuration"] = task["configuration"]
        changed = file_change(
            host.project_root, ".concorde/config.json", canonical(value) + "\n"
        )
        apply_files(
            host.project_root,
            [changed],
            {changed["path"]},
            verify=lambda: SpecRepository(host.project_root, host.package_root),
        )
        return {
            "output": typed(
                "concorde-configure-response",
                {"status": "applied", "configuration": task["configuration"]},
            ),
            "route": END,
        }

    def apply(state):
        if "proposal" not in task:
            raise SpecError(
                "apply requires the complete typed proposal", "invalid_input"
            )
        proposal = task["proposal"]
        value = apply_project_proposal(
            host.project_root,
            host.package_root,
            {
                "type_id": proposal["type_id"],
                "schema_version": proposal["schema_version"],
                **proposal["data"],
            },
        )
        return {
            "output": typed(
                OPERATION_CONTRACTS[operation][1],
                {"status": "applied", "proposal": None, "files": value["files"]},
            ),
            "route": END,
        }

    def propose(state):
        if not {"name", "configuration"}.issubset(task):
            raise SpecError(
                "initialization proposal requires name and configuration",
                "invalid_input",
            )
        value = project_proposal(
            host.project_root,
            host.package_root,
            task["name"],
            task["configuration"],
            task.get("target_id", "module.project"),
        )
        proposal = typed(
            "concorde-project-proposal",
            {key: value[key] for key in ("action", "base_digest", "files")},
        )
        return {
            "output": typed(
                OPERATION_CONTRACTS[operation][1],
                {
                    "status": "proposed",
                    "proposal": proposal,
                    "files": [x["path"] for x in value["files"]],
                },
            ),
            "route": END,
        }

    return {
        "select_action": select_action,
        "configure": configure,
        "apply": apply,
        "propose": propose,
    }
