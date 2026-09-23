"""The Operation catalog: the checked declarations of every Operation and the registration entry.

Each Operation is declared once in ``operations/<name>.py`` of the package root; the package
``operations/__init__.py`` lists the declared module names in ``OPERATIONS``. The loader imports
exactly those, refuses the whole catalog when any declaration breaks a rule of the catalog
reference, and hands admission the capability declarations it decides from. ``register_types`` is
the one explicit registration entry of every process that checks typed values: it loads each
owner's record module, which registers the owner's types with Spec tooling, and registers every
declaration's request and response.
"""

from __future__ import annotations

import importlib
import sys
import uuid
from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

from ..spec.typed_data import TypedDataError, register

PACKAGE_ROOT = Path(__file__).resolve().parents[3]

# The routed control-flow kinds; ``graph`` is reserved until an Operation of that kind exists.
KINDS = ("host", "agent-call", "pi-workflow")

# Every field a declaration states, with its Python type.
FIELDS: dict[str, type | tuple[type, ...]] = {
    "KIND": str,
    "PUBLIC": bool,
    "DETERMINISTIC": bool,
    "OWNER": str,
    "AGENTS": tuple,
    "USES": tuple,
    "REQUEST": dict,
    "RESPONSE": dict,
    "REQUEST_VERSION": int,
    "RESPONSE_VERSION": int,
    "MUTATION": dict,
    "WORKSPACE": str,
    "TARGET": dict,
    "DEFAULT_TASK": (str, type(None)),
    "CONFIGURATION": str,
    "ENTRY_POINT": str,
}


class CatalogError(ValueError):
    """A declaration breaks a catalog rule; the whole catalog is refused."""

    code = "invalid_input"

    def __init__(self, declaration: str, field: str, message: str):
        super().__init__(f"operations/{declaration}.py {field}: {message}")
        self.declaration = declaration
        self.field = field


def _refused(declaration: str, field: str, message: str) -> CatalogError:
    return CatalogError(declaration, field, message)


@dataclass(frozen=True)
class Operation:
    """One loaded declaration."""

    id: str
    public_name: str
    kind: str
    public: bool
    deterministic: bool
    owner: str
    agents: tuple[tuple[str, str], ...]
    uses: tuple[str, ...]
    request: dict
    response: dict
    request_version: int
    response_version: int
    # The capability declaration admission reads (contract.admission.capability-declaration).
    declaration: dict

    @property
    def request_type(self) -> str:
        return f"{self.public_name}-request"

    @property
    def response_type(self) -> str:
        return f"{self.public_name}-response"

    def mirror(self) -> dict:
        """The record of the ``concorde.operations`` metadata mirror."""
        return {
            "id": self.id,
            "public_name": self.public_name,
            "kind": self.kind,
            "public": self.public,
            "deterministic": self.deterministic,
            "owner": self.owner,
            "agents": [
                {"agent": agent, "phase": phase} for agent, phase in self.agents
            ],
            "uses": list(self.uses),
        }


def public_name(module_name: str) -> str:
    return "concorde-" + module_name.replace("_", "-")


def _inventory(root: Path) -> ModuleType:
    """The ``operations`` package of ``root``.

    The running package's own declarations import normally under the name ``operations``; any
    other root (a package under check) loads under a private name so validations of different
    roots in one process never share modules.
    """
    if root.resolve() == PACKAGE_ROOT:
        if str(PACKAGE_ROOT) not in sys.path:
            sys.path.insert(0, str(PACKAGE_ROOT))
        return importlib.import_module("operations")
    init = root / "operations/__init__.py"
    if init.is_symlink() or not init.is_file():
        raise _refused("__init__", "OPERATIONS", "operations/__init__.py is missing")
    name = f"_concorde_operations_{uuid.uuid4().hex}"
    spec = spec_from_file_location(
        name, init, submodule_search_locations=[str(root / "operations")]
    )
    if spec is None or spec.loader is None:
        raise _refused("__init__", "OPERATIONS", "operations/__init__.py is unreadable")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _agent_definitions() -> dict:
    """Every Agent definition by name; a phase is valid only as its Agent's own."""
    from ..harness.worker_profile import agent_definition, agent_names

    return {name: agent_definition(name) for name in agent_names()}


def _load(name: str, module: ModuleType) -> Operation:
    from ..harness.admission import check_declaration

    for field, kind in FIELDS.items():
        if not hasattr(module, field):
            raise _refused(name, field, "missing field")
        value = getattr(module, field)
        if not isinstance(value, kind) or (kind is int and type(value) is not int):
            raise _refused(name, field, "wrong type")
    kind = module.KIND
    if kind not in KINDS:
        raise _refused(name, "KIND", f"{kind!r} is not a routed kind")
    if module.DETERMINISTIC != (kind == "host"):
        raise _refused(name, "DETERMINISTIC", "must be true exactly for kind host")
    definitions = _agent_definitions()
    steps = module.AGENTS
    for step in steps:
        if (
            not isinstance(step, tuple)
            or len(step) != 2
            or not all(isinstance(item, str) for item in step)
        ):
            raise _refused(name, "AGENTS", "each step is (agent, phase)")
        if step[0] not in definitions:
            raise _refused(name, "AGENTS", f"no Agent definition for {step[0]!r}")
        if step[1] != definitions[step[0]].phase:
            raise _refused(
                name, "AGENTS", f"{step[1]!r} is not the phase of {step[0]!r}"
            )
    if kind == "host" and steps:
        raise _refused(name, "AGENTS", "a host Operation runs no Agent")
    if kind == "agent-call" and len(steps) != 1:
        raise _refused(name, "AGENTS", "an agent-call Operation runs exactly one Agent")
    if kind == "pi-workflow" and not steps:
        raise _refused(name, "AGENTS", "a pi-workflow Operation runs Agents")
    if kind == "agent-call" and module.ENTRY_POINT != definitions[steps[0][0]].hook:
        raise _refused(
            name,
            "ENTRY_POINT",
            "an agent-call entry point is the hook its Agent's definition names",
        )
    if not all(isinstance(item, str) for item in module.USES) or len(
        set(module.USES)
    ) != len(module.USES):
        raise _refused(name, "USES", "public names, each once")
    if type(module.REQUEST_VERSION) is not int or module.REQUEST_VERSION < 1:
        raise _refused(name, "REQUEST_VERSION", "a positive version")
    if type(module.RESPONSE_VERSION) is not int or module.RESPONSE_VERSION < 1:
        raise _refused(name, "RESPONSE_VERSION", "a positive version")
    external = public_name(name)
    declaration = {
        "capability": external,
        "public": module.PUBLIC,
        "model_backed": not module.DETERMINISTIC,
        "request_type": f"{external}-request",
        "response_type": f"{external}-response",
        "mutation": module.MUTATION,
        "workspace": module.WORKSPACE,
        "target": module.TARGET,
        "default_task": module.DEFAULT_TASK,
        "configuration": module.CONFIGURATION,
        "entry_point": module.ENTRY_POINT,
    }
    try:
        check_declaration(declaration)
    except (ValueError, ImportError) as error:
        raise _refused(
            name, getattr(error, "field", "") or "declaration", str(error)
        ) from error
    return Operation(
        id=name.replace("_", "-"),
        public_name=external,
        kind=kind,
        public=module.PUBLIC,
        deterministic=module.DETERMINISTIC,
        owner=module.OWNER,
        agents=tuple(steps),
        uses=tuple(module.USES),
        request=module.REQUEST,
        response=module.RESPONSE,
        request_version=module.REQUEST_VERSION,
        response_version=module.RESPONSE_VERSION,
        declaration=declaration,
    )


def load_catalog(root: Path = PACKAGE_ROOT) -> dict[str, Operation]:
    """Every declared Operation by public name, in ``OPERATIONS`` order, or ``CatalogError``."""
    inventory = _inventory(root)
    listed = getattr(inventory, "OPERATIONS", None)
    if not isinstance(listed, tuple) or not all(isinstance(n, str) for n in listed):
        raise _refused("__init__", "OPERATIONS", "a tuple of module names")
    if len(set(listed)) != len(listed):
        raise _refused("__init__", "OPERATIONS", "each module is listed once")
    present = {
        path.stem
        for path in (root / "operations").glob("*.py")
        if path.stem != "__init__"
    } | {path.parent.name for path in (root / "operations").glob("*/__init__.py")}
    for name in sorted(present - set(listed)):
        raise _refused(name, "OPERATIONS", "module is not listed")
    loaded: dict[str, Operation] = {}
    for name in listed:
        if name not in present:
            raise _refused(name, "OPERATIONS", "listed module is missing")
        try:
            module = importlib.import_module(f"{inventory.__name__}.{name}")
        except CatalogError:
            raise
        except Exception as error:  # noqa: BLE001 - any import failure refuses the catalog
            raise _refused(name, "module", f"cannot be imported: {error}") from error
        operation = _load(name, module)
        loaded[operation.public_name] = operation
    for operation in loaded.values():
        for child in operation.uses:
            if child not in loaded or not loaded[child].public:
                raise _refused(
                    operation.id.replace("-", "_"),
                    "USES",
                    f"{child!r} is not cataloged",
                )
            if child == operation.public_name:
                raise _refused(
                    operation.id.replace("-", "_"),
                    "USES",
                    "an Operation cannot use itself",
                )

    def visit(name: str, chain: tuple[str, ...]) -> None:
        if name in chain:
            raise _refused(
                loaded[chain[0]].id.replace("-", "_"),
                "USES",
                "composition is cyclic: " + " -> ".join((*chain, name)),
            )
        for child in loaded[name].uses:
            visit(child, (*chain, name))

    for name in loaded:
        visit(name, ())
    return loaded


CATALOG = load_catalog()
# Only Operations; Agents are not cataloged.
OPERATION_NAMES = tuple(CATALOG)
PUBLIC_OPERATIONS = tuple(name for name, item in CATALOG.items() if item.public)


def declarations() -> dict[str, dict]:
    """The capability declarations admission decides from, by capability name."""
    return {name: dict(item.declaration) for name, item in CATALOG.items()}


# The owners' registering modules; loading one registers that owner's typed values, and
# Planning's scope registers its component request rule with Candidate worktrees.
RECORD_MODULES = (
    "..spec.initialize",
    "..harness.configuration",
    "..harness.context",
    "..harness.native_result",
    "..issues.shapes",
    "..planning.records",
    "..planning.scope",
    "..review.records",
)


def register_catalog(catalog: dict[str, Operation]) -> tuple[str, ...]:
    """Register each declaration's request and response; a schema that does not register refuses."""
    registered = []
    for operation in catalog.values():
        for type_id, version, schema, field in (
            (
                operation.request_type,
                operation.request_version,
                operation.request,
                "REQUEST",
            ),
            (
                operation.response_type,
                operation.response_version,
                operation.response,
                "RESPONSE",
            ),
        ):
            try:
                register(type_id, version, schema)
            except TypedDataError as error:
                raise _refused(
                    operation.id.replace("-", "_"), field, str(error)
                ) from error
            registered.append(type_id)
    return tuple(registered)


def register_types() -> tuple[str, ...]:
    """Register every owner's typed values and every declaration's request and response.

    Idempotent; returns the registered request and response type identities in catalog order.
    """
    for name in RECORD_MODULES:
        importlib.import_module(name, __package__)
    return register_catalog(CATALOG)


def operation(name: str) -> Operation:
    """One cataloged Operation by public name."""
    return CATALOG[name]


def mirror(catalog: dict[str, Any] | None = None) -> list[dict]:
    """The ``concorde.operations`` mirror records of ``catalog``, sorted by identity."""
    return sorted(
        (item.mirror() for item in (catalog or CATALOG).values()),
        key=lambda record: record["id"],
    )
