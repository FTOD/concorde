"""Global Module discovery for the main entry and for every discovering operation."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ..distribution.build import load_model_instructions
from ..harness.configuration import load_configuration
from ..harness.context import (
    DiscoveryContext,
    context_documents,
    materialize_documents,
    recheck_discovery_context,
    resolve_discovery_context,
)
from ..harness.host import (
    OperationHost,
    protocol_documents,
    run_worker,
    worker_description,
    worker_invocation,
)
from ..harness.permissions import PermissionPolicyError, PolicyBinding, compile_policy
from ..harness.worker_profile import worker_profile
from ..spec.contracts import DISCOVERY_NODES, DISCOVERY_OPERATIONS, MAIN_OPERATION
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import OPERATION_CONTRACTS, typed


class MainInvocation:
    """Global Module discovery followed by fresh target workers."""

    def __init__(
        self, operation: str, configuration: dict, task: dict, host: OperationHost
    ):
        self.operation, self.configuration, self.task, self.host = (
            operation,
            configuration,
            task,
            host,
        )
        if operation not in DISCOVERY_OPERATIONS:
            raise SpecError(
                "operation does not support main discovery", "unknown_operation"
            )
        self.action = (
            task.get("action", "route") if operation == MAIN_OPERATION else "route"
        )
        self.repository = SpecRepository(host.project_root, host.package_root)
        self.entry = self.repository.select(self.repository.entry_target)
        if self.entry.kind != "module":
            raise SpecError(
                "the project entry target must be a Module for main discovery",
                "invalid_entry_target",
            )
        if task.get("focus_id") and not task.get("target_id"):
            raise SpecError("a focus hint requires a target hint", "invalid_focus")
        if task.get("target_id"):
            self.repository.select(task["target_id"], task.get("focus_id"))
        self.discovered = [self.entry.id]
        self.last_context: str | None = None
        self.last_snapshot: DiscoveryContext | None = None
        self.completed: list[str] = []

    def main_response(
        self,
        outcome: str,
        answer: str = "",
        *,
        routes=(),
        topology_proposal=None,
        application=None,
        files=(),
        blockers=(),
    ) -> dict:
        if self.last_context is None or self.last_snapshot is None:
            raise SpecError(
                "main response has no discovery context", "invalid_completion"
            )
        return typed(
            "concorde-main-response",
            {
                "action": self.action,
                "entry_target": self.entry.id,
                "context_id": self.last_context,
                "outcome": outcome,
                "answer": answer,
                "discovered_targets": list(self.discovered),
                "routes": list(routes),
                "topology_proposal": topology_proposal,
                "application": application,
                "files": list(files),
                "blockers": list(blockers),
                "completed_operations": list(self.completed),
                "workspace": self.last_snapshot.value["workspace"],
            },
        )

    def operation_response(
        self, outcome: str, answer: str = "", *, blockers=()
    ) -> dict:
        if self.last_context is None:
            raise SpecError(
                "main response has no discovery context", "invalid_completion"
            )
        return typed(
            OPERATION_CONTRACTS[self.operation][1],
            {
                "target_id": self.entry.id,
                "focus_id": None,
                "change_id": self.task.get("change_id"),
                "context_id": self.last_context,
                "outcome": outcome,
                "answer": answer,
                "artifacts": [],
                "blockers": list(blockers),
                "checks": [],
                "completed_operations": list(self.completed),
                **({"reviews": []} if self.operation == "concorde-review" else {}),
            },
        )

    def stage(self, phase: str, occurrence: int) -> dict:
        role = DISCOVERY_NODES[self.action]
        prompt = load_model_instructions(self.host.package_root, role)
        agent = worker_profile(prompt.binding.agent)
        snapshot = resolve_discovery_context(
            self.repository,
            tuple(self.discovered),
            operation=self.operation,
            phase=phase,
            task=self.task["task"],
            action=self.action,
            target_hint=self.task.get("target_id"),
            focus_hint=self.task.get("focus_id"),
            constraints=tuple(self.task.get("constraints", [])),
            instructions=prompt.body,
            agent=agent,
        )
        self.last_context = snapshot.id
        self.last_snapshot = snapshot
        before_registry = self.repository.registry_bytes
        with tempfile.TemporaryDirectory(prefix="concorde-discovery-") as directory:
            capsule = Path(directory)
            project_workspace = agent.workspace == "project"
            project = self.host.project_root if project_workspace else capsule
            context_file = capsule / "context.json"
            # The index is written beside byte-identical copies of every document it lists; the
            # worker opens them on demand instead of receiving their bodies in its input.
            granted = context_documents(self.repository, snapshot.value)
            if self.host.mode != "describe-policy":
                context_file.write_text(snapshot.serialized + "\n")
                if not project_workspace:
                    materialize_documents(capsule, granted)
            roles = {prompt.effects.reads[0]: ("context.json", *sorted(granted))}
            try:
                policy = compile_policy(
                    prompt.effects,
                    PolicyBinding(
                        self.operation, phase, occurrence, role, role, write_roles=()
                    ),
                    roles,
                )
            except PermissionPolicyError as error:
                raise SpecError(str(error), "permission_denied") from error
            receipt = {
                "schema_version": 16,
                "entry_target": self.entry.id,
                "phase": phase,
                "context_id": snapshot.id,
                "source_digest": snapshot.id,
                "registry_digest": digest(before_registry),
                "discovered_targets": list(self.discovered),
                "role_paths": {key: list(value) for key, value in roles.items()},
            }
            value = typed(
                "concorde-main-stage-context",
                {
                    "snapshot": typed("concorde-discovery-context", snapshot.value),
                },
            )
            invocation = worker_invocation(
                self.configuration,
                operation=self.operation,
                stage=phase,
                prompt=prompt,
                workspace=project,
                context_value=value,
                receipt=receipt,
                policy=policy,
                protocol=protocol_documents(snapshot.value, granted),
            )
            self.host.descriptions.append(
                worker_description(
                    prompt,
                    invocation,
                    policy,
                    operation=self.operation,
                    phase=phase,
                    context_id=snapshot.id,
                    project_root=str(project),
                    discovered_targets=list(self.discovered),
                )
            )
            if self.host.mode == "describe-policy":
                return {
                    "context_id": snapshot.id,
                    "outcome": "described",
                    "answer": "",
                    "expand_targets": [],
                    "routes": [],
                    "blockers": [],
                }
            from ..harness.operation_node import OperationNode

            result = None

            def launch_worker(context):
                nonlocal result
                result, data = run_worker(
                    self.host,
                    invocation,
                    prompt,
                    operation=self.operation,
                    stage=phase,
                    target_id=self.entry.id,
                    result_type="concorde-main-stage-result",
                )
                return data

            data = OperationNode(agent.name).invoke(value, launch_worker)
            self._validate_result(snapshot, phase, data)
            if (
                read_file(self.repository.root, self.repository.registry_path)
                != before_registry
            ):
                raise SpecError(
                    "registry changed during main discovery", "stale_context"
                )
            recheck_discovery_context(self.repository, snapshot)
            if load_configuration(self.repository.root) != self.configuration:
                raise SpecError(
                    "configuration changed during main discovery",
                    "configuration_mismatch",
                )
            if context_file.read_text() != snapshot.serialized + "\n":
                raise SpecError("frozen discovery capsule changed", "stale_context")
            self.host.evidence.append(result)
            return data

    def _validate_result(
        self, snapshot: DiscoveryContext, phase: str, data: dict
    ) -> None:
        if data["context_id"] != snapshot.id:
            raise SpecError(
                "main returned a different discovery context identity",
                "incompatible_handoff",
            )
        outcome = data["outcome"]
        expansions, routes, blockers = (
            data["expand_targets"],
            data["routes"],
            data["blockers"],
        )
        topology = data["topology_design"]
        if phase == "route":
            if outcome == "completed":
                if (
                    self.operation != MAIN_OPERATION
                    or self.action != "ask"
                    or expansions
                    or routes
                    or blockers
                    or topology is not None
                    or not data["answer"].strip()
                ):
                    raise SpecError(
                        "direct main answers require only an answer from admitted Spec context or workspace metadata",
                        "invalid_completion",
                    )
            elif outcome == "expand":
                if not expansions or routes or blockers or topology is not None:
                    raise SpecError(
                        "expand requires only nonempty Module targets",
                        "invalid_completion",
                    )
            elif outcome == "routed":
                if (
                    self.action == "ask"
                    or expansions
                    or not routes
                    or blockers
                    or topology is not None
                ):
                    raise SpecError(
                        "routed requires only nonempty worker routes",
                        "invalid_completion",
                    )
            elif outcome == "topology_proposed":
                if (
                    self.action != "design-topology"
                    or expansions
                    or routes
                    or blockers
                    or topology is None
                ):
                    raise SpecError(
                        "topology design has inconsistent fields", "invalid_completion"
                    )
            elif outcome in {"spec_incomplete", "unsupported", "conflicting", "failed"}:
                if (
                    expansions
                    or routes
                    or topology is not None
                    or (outcome == "spec_incomplete" and not blockers)
                ):
                    raise SpecError(
                        "blocked main routing has inconsistent fields",
                        "invalid_completion",
                    )
            else:
                raise SpecError(
                    "route phase returned an unsupported outcome", "invalid_completion"
                )
        else:
            raise SpecError("main returned an unsupported phase", "invalid_completion")
        # run_worker has admitted every referenced observation against this exact discovery.
        if blockers and outcome in {
            "completed",
            "routed",
            "expand",
            "topology_proposed",
        }:
            raise SpecError(
                "successful discovery cannot retain task blockers", "invalid_completion"
            )

    def discover_routes(self) -> tuple[list[dict], dict | None]:
        from .discovery_graph import build_discovery_graph

        state = build_discovery_graph(self.discovery_nodes().__getitem__).invoke(
            {"occurrence": 0},
            {"recursion_limit": 2 * (len(self.repository.targets) + 1) + 3},
        )
        return state["routes"], state["decision"]

    def discovery_nodes(self):
        routable_targets = sum(
            target.kind == "module" for target in self.repository.targets.values()
        )

        def decide(state):
            occurrence = state.get("occurrence", 0)
            if occurrence > routable_targets:
                raise SpecError("main discovery step limit exceeded", "context_limit")
            decision = self.stage("route", occurrence)
            route = (
                "finish"
                if self.host.mode == "describe-policy"
                else {"expand": "expand_context", "routed": "bind_routes"}.get(
                    decision["outcome"], "finish"
                )
            )
            return {"occurrence": occurrence, "decision": decision, "route": route}

        def expand_context(state):
            decision = state["decision"]
            admitted_text = self.stage_context_text(decision)
            for target_id in decision["expand_targets"]:
                if target_id in self.discovered:
                    raise SpecError(
                        "main discovery requested an already admitted target",
                        "invalid_completion",
                    )
                if (
                    target_id != self.task.get("target_id")
                    and target_id not in admitted_text
                ):
                    raise SpecError(
                        "main discovery requested a target absent from admitted Specs",
                        "incompatible_handoff",
                        target_id,
                    )
                target = self.repository.select(target_id)
                if target.kind != "module":
                    raise SpecError(
                        "main discovery accepts only Module Specs",
                        "permission_denied",
                        target_id,
                    )
                self.discovered.append(target_id)
            return {"occurrence": state["occurrence"] + 1}

        def bind_routes(state):
            decision = state["decision"]
            original_constraints = self.task.get("constraints", [])
            routing_text = self.stage_context_text(decision)
            bound_routes = []
            for index, route in enumerate(decision["routes"]):
                self.repository.select(route["target_id"], route["focus_id"])
                if (
                    route["target_id"] not in self.discovered
                    and route["target_id"] not in routing_text
                ):
                    raise SpecError(
                        "main routed a target absent from admitted Module Specs",
                        "incompatible_handoff",
                        route["target_id"],
                    )
                if self.operation != MAIN_OPERATION:
                    mismatches = [
                        field
                        for field, expected in (
                            ("task", self.task["task"]),
                            ("constraints", original_constraints),
                        )
                        if field in route and route[field] != expected
                    ]
                    if mismatches:
                        fields = ", ".join(
                            f"routes[{index}].{field}" for field in mismatches
                        )
                        raise SpecError(
                            f"main route changed single-target task intent: {fields}",
                            "incompatible_handoff",
                            fields,
                        )
                    route = {
                        **route,
                        "task": self.task["task"],
                        "constraints": list(original_constraints),
                    }
                else:
                    missing = [
                        field for field in ("task", "constraints") if field not in route
                    ]
                    if missing:
                        raise SpecError(
                            f"main route omitted fields: routes[{index}]."
                            + ", ".join(missing),
                            "incompatible_handoff",
                        )
                    if any(
                        item not in route["constraints"]
                        for item in original_constraints
                    ):
                        raise SpecError(
                            f"main route dropped a user constraint: routes[{index}].constraints",
                            "incompatible_handoff",
                        )
                bound_routes.append(route)
            return {"routes": bound_routes, "decision": None}

        def finish(state):
            if self.host.mode == "describe-policy":
                if self.action != "ask" and self.task.get("target_id"):
                    return {
                        "routes": [
                            {
                                "target_id": self.task["target_id"],
                                "focus_id": self.task.get("focus_id"),
                                "task": self.task["task"],
                                "constraints": self.task.get("constraints", []),
                            }
                        ],
                        "decision": None,
                    }
            else:
                self.completed.append("concorde-router-route")
            return {"routes": []}

        nodes = {
            "decide": decide,
            "expand_context": expand_context,
            "bind_routes": bind_routes,
            "finish": finish,
        }
        return nodes

    def stage_context_text(self, decision: dict) -> str:
        """Return only source text bound to the decision's complete context identity."""

        if decision["context_id"] != self.last_context or self.last_snapshot is None:
            raise SpecError(
                "main route no longer matches its discovery context", "stale_context"
            )
        value = self.last_snapshot.value
        granted = context_documents(self.repository, value)
        return "\n".join(
            granted[source["path"]].decode("utf-8") for source in value["documents"]
        )

    def select_one(self) -> tuple[dict | None, dict | None]:
        return self.select_discovered(*self.discover_routes())

    def select_discovered(self, routes, decision) -> tuple[dict | None, dict | None]:
        """Admit the result of this invocation's executed discovery subgraph."""
        if decision is not None:
            outcome = (
                "described"
                if self.host.mode == "describe-policy"
                else decision["outcome"]
            )
            return None, self.operation_response(
                outcome, decision["answer"], blockers=decision["blockers"]
            )
        if len(routes) != 1:
            raise SpecError(
                f"{self.operation} requires one owning target; route cross-target work through a coordinating Module",
                "ambiguous_route",
            )
        self.completed.append("concorde-router-route")
        return routes[0], None

    def run_answer(self) -> dict:
        _, decision = self.discover_routes()
        return self.answer_response(decision)

    def answer_response(self, decision):
        if decision is None:
            raise SpecError(
                "questions require a direct answerer result", "invalid_completion"
            )
        outcome = (
            "described" if self.host.mode == "describe-policy" else decision["outcome"]
        )
        return self.main_response(
            outcome, decision["answer"], blockers=decision["blockers"]
        )
