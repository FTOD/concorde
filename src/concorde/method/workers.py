"""The standard worker sequence of Method's Operations (specs/concorde/method/workers.md).

A worker-backed step of a Method Operation computes the grant for its task type and Modules from
the workspace's Specs through Spec core, lowers every writable level to read when the provider
withholds writes, and projects the result into the worker harness's grant input; it composes the
task instructions with the definitions of the glossary terms the grant carries and the rules about
Spec gaps; it resolves the worker's backend, model and limits through the worker harness's
configuration reader; and it hands everything, with its round validation, to the worker harness,
which launches, audits, resumes and records the worker. The round validation checks glossary
ownership, then the configured checks when the step asks for them, then the step's own validation;
glossary ownership is checked once more after the worker run, whatever its status.

Every Method Operation admits its Modules against the workspace's Specs (``specs.admission``),
begins with ``check_worker_models``, the admission of all its workers against the worker
configuration and the model map, and one that may run unbound gives the runner ``runtime_paths`` to
link into its checkout.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Callable

from ..execution.context import (
    Continue,
    Provider,
    RunContext,
    Stop,
    component,
)
from ..execution.operations.catalog import OPERATIONS
from .specs import admission, spec_cause
from ..kernel.errors import evidence
from ..kernel.tracing import layout
from ..worker_harness import models
from ..worker_harness.workers import (
    Refusal,
    RoundValidation,
    WorkerRequest,
    run_worker as launch,
)

# Task types whose workers may change files; an unbound run never launches one.
WRITING_TASK_TYPES = ("specify", "implement", "code-to-spec")
# The fields of Spec core's grant the worker harness's grant input takes; the Modules, terms and
# glossary path stay with Method.
GRANT_INPUT_FIELDS = ("task_type", "entries", "context_identity")
# How much of a failing check's log a resume prompt carries.
LOG_TAIL = 20_000

CONFIG = models.CONFIG
# How an Operation treats each error code of a worker run record: the reason it cannot handle it,
# the explanation, the options it offers the main agent and its recommendation.
WORKER_HANDLING = {
    "audit_violation": (
        "permission",
        "an Operation never widens a grant and never retries with a wider one; giving the "
        "task the path (creating the file and binding it to a bound Module, or binding more "
        "Modules) is the task level's decision",
        [
            "create the file and bind it to a bound Module at the task level, then run the "
            "Operation again",
            "bind the Module that owns the path and run the Operation again",
            "discard the stray change and run the Operation with a narrower goal",
        ],
    ),
    "checks_failed": (
        "decision",
        "the Operation used every resume round it is configured with; whether to narrow the "
        "goal, change the Spec or allow more rounds is the main agent's decision",
        [
            "run the Operation again with a narrower goal or more --rounds",
            "run understand to check whether the Spec supports the change",
            "run test to get an interpretation of the failures",
        ],
    ),
    "worker_blocked": (
        "decision",
        "the worker's blocker needs a decision, a permission or a Spec change above the "
        "Operation",
        [
            "follow the worker's options in the cause",
            "run specify when the worker names a Spec gap",
        ],
    ),
    "worker_failed": (
        "decision",
        "the Operation does not rerun a worker that failed; rerunning or changing the task is "
        "the main agent's decision",
        ["follow the worker's options in the cause", "run the Operation again"],
    ),
    "worker_timeout": (
        "exhausted",
        "the Operation passes the configured limits to Workers and does not raise them; "
        f"raising limits.timeout_seconds in {CONFIG} is the main agent's decision",
        [
            f"raise limits.timeout_seconds in {CONFIG}",
            "run the Operation with a narrower goal",
        ],
    ),
    "worker_limit_reached": (
        "exhausted",
        "the Operation passes the configured limits to Workers and does not raise them; "
        f"raising limits.max_turns or limits.max_budget_usd in {CONFIG} is the main agent's "
        "decision",
        [
            f"raise limits.max_turns or limits.max_budget_usd in {CONFIG}",
            "run the Operation with a narrower goal",
        ],
    ),
    "worker_result_invalid": (
        "capability",
        "the Operation cannot repair a worker's answer and does not relaunch a worker",
        ["run the Operation again", "inspect the transcript in the cause's evidence"],
    ),
}
ENVIRONMENT_HANDLING = (
    "environment",
    "the failure lies in the environment the Operation runs in, which it cannot change",
    ["repair the environment named in the cause and run the Operation again"],
)


def declared_workers() -> dict[str, tuple[str, ...]]:
    """Every Operation the installed parts register, with its worker ids: the names a worker
    configuration may use. An Operation whose runs each name their task type, such as
    ``general``, declares none and is listed all the same."""
    return {
        name: OPERATIONS.get(name).workers
        for name in OPERATIONS
        if OPERATIONS.get(name).kind == "operation"
    }


def runtime_paths(checkout: Path) -> tuple[str, ...]:
    """The runtime-path resolver of a Method Operation that may run unbound: ``runtime`` of the
    worker configuration committed in ``checkout``, or its default; nothing when that file
    cannot be read or is not valid, which the run's admission then refuses on the same file."""
    try:
        return models.runtime(models.load(checkout, declared_workers()))
    except models.ModelConfigError:
        return ()


def model_cause(error: models.ModelConfigError, explanation: str) -> dict:
    """The configuration reader's refusal as the component link under Method's own."""
    reason = models.HANDLING.get(error.code, ("input",))[0]
    return component(
        "Workers (worker configuration)", error.code, str(error), reason, explanation
    )


def check_worker_models(context: RunContext):
    """The admission step every Method Operation begins with: check every worker the Operation
    may launch against the machine's model map at once, and the configuration's Operation and
    worker names against every Operation the installed parts register, so that the run never
    stops at a later worker after earlier ones ran; stop ``failed`` with
    ``worker_model_unavailable`` before any worker launches otherwise."""
    try:
        declared = declared_workers()
        models.check_mapped(
            models.load(context.worktree, declared), declared, operation=context.name
        )
    except models.ModelConfigError as error:
        path = models.config_path(context.worktree).as_posix()
        reason = models.HANDLING.get(error.code, ("input",))[0]
        return context.fail(
            "failed",
            "worker_model_unavailable",
            f"The workers of {context.name} could not be configured ({error.code}).",
            f"the models of the workers {context.name} may launch in {context.worktree} cannot "
            f"all be settled: {error.code}: {error} (configuration file {path}); the run checks "
            "them all when it is admitted, so no worker launched",
            reason=reason,
            explanation="an Operation runs each worker on the program and model the worker "
            "configuration chooses for it, through the machine's model map, and never guesses, "
            "repairs or falls back from any of them",
            evidence=[evidence("worker_configuration", path, f"{error.code}: {error}")],
            causes=[
                model_cause(
                    error,
                    "Workers reads the worker configuration and the model map and changes "
                    "neither",
                )
            ],
            options=(
                [
                    "write or correct this machine's model map as the error says, giving each "
                    "project model name it names its local id on that backend; the map is the "
                    "user's and is never committed"
                ]
                if error.code
                in ("model_map_missing", "model_map_invalid", "model_unmapped")
                else [
                    f"correct {path} as the error says and commit it; an unbound run reads the "
                    "committed file of its checkout"
                ]
            ),
        )
    return Continue()


def operation(*arguments, **fields) -> Provider:
    """A Method Operation's definition: the admission of its Modules against the workspace's
    Specs, its steps preceded by the admission of its workers and, when it may run unbound, the
    runtime-path resolver of its checkout."""
    chosen = Provider(*arguments, **fields)
    return replace(
        chosen,
        admit=admission(),
        steps=(check_worker_models, *chosen.steps),
        runtime_paths=runtime_paths if chosen.binding == "optional" else None,
    )


def interpreter_roots(interpreter: str, home: Path | None = None) -> tuple[Path, ...]:
    """What must be readable for a worker to run ``interpreter``.

    The sandbox makes a path readable at its real location, so the environment the interpreter
    belongs to and the installation it resolves to are not enough when the way between them
    passes through a symbolic link, such as uv's ``cpython-3.9-linux-x86_64-gnu`` pointing to
    ``cpython-3.9.25-linux-x86_64-gnu``: the directory holding each link on the way must be
    readable too. A directory that is the home itself or holds it is never included.
    """
    home = Path(os.path.realpath(home or Path.home()))
    roots = [Path(interpreter).parent.parent]
    pending = list(Path(interpreter).parts[1:])
    current = Path("/")
    hops = 0
    while pending and hops < 40:
        part = pending.pop(0)
        if part in ("", "."):
            continue
        if part == "..":
            current = current.parent
            continue
        candidate = current / part
        if candidate.is_symlink():
            hops += 1
            roots.append(current)
            target = Path(os.readlink(candidate))
            if target.is_absolute():
                current = Path("/")
                pending = list(target.parts[1:]) + pending
            else:
                pending = list(target.parts) + pending
        else:
            current = candidate
    roots.append(Path(os.path.realpath(interpreter)).parent.parent)
    return tuple(
        dict.fromkeys(
            root
            for root in roots
            if root.exists()
            and root != Path("/usr")
            and not (root == home or root in home.parents)
        )
    )


def withhold_writes(value: dict) -> dict:
    """A grant with every ``rw`` entry lowered to ``ro``; the entry list is otherwise unchanged."""
    return {
        **value,
        "entries": [
            {**entry, "level": "ro"} if entry["level"] == "rw" else dict(entry)
            for entry in value["entries"]
        ],
    }


def grant_input(value: dict) -> dict:
    """Spec core's grant projected into the worker harness's grant input: its task type, entries
    and context identity, unchanged."""
    return {name: value[name] for name in GRANT_INPUT_FIELDS}


def writable(entries: list[dict], path: str | None) -> bool:
    """Whether the grant's ``entries`` make ``path`` writable, by itself or below a directory."""
    if path is None:
        return False
    return any(
        entry["level"] == "rw"
        and (
            entry["path"] == path
            or (entry["path"].endswith("/") and path.startswith(entry["path"]))
        )
        for entry in entries
    )


def spec_rule(task_type: str) -> str:
    """The rule about promises the Spec does not state, which depends on the task type."""
    if task_type == "code-to-spec":
        return (
            "- Describing the code you read in the bound Modules' Specs is your task. Record "
            "behaviour as it is; behaviour whose intent the code does not settle is reported as "
            "an open question, never written as a promise.\n"
        )
    if task_type == "review-code":
        return (
            "- When the Spec neither requires nor forbids behaviour you see, do not infer a "
            "promise from code: report it as a `spec-gap` finding whose basis is the passage that "
            "would have to settle it.\n"
        )
    if task_type == "understand":
        return (
            "- When the Spec does not state a promise the goal needs, do not infer it from code: "
            "report it as a Spec gap in your assessment and end `ok`.\n"
        )
    if task_type in ("review-spec", "review-architecture"):
        return (
            "- When the Spec does not state a promise, or you lack a document you need, do not "
            "infer it from code: report it as a finding, as your task says, and go on reviewing. "
            "Return `blocked` only when you cannot review at all.\n"
        )
    return (
        "- When the Spec does not state a promise you need, do not infer it from code: return "
        "`blocked` and describe the missing promise.\n"
    )


def terms(value: dict) -> str:
    """The glossary section of the instructions: the definitions of the words the bound Modules'
    documents link, and, when the glossary is writable, which of its entries the worker may
    change."""
    from ..spec.glossary import plain_definition

    entries = value.get("terms") or []
    glossary = value.get("glossary")
    changeable = writable(value["entries"], glossary)
    if not entries and not changeable:
        return ""
    lines = ["## Terms\n\n"]
    if entries:
        lines.append(
            "The words your documents link to the glossary mean the following; a term link's "
            "fragment is the identity in brackets.\n\n"
        )
        lines.extend(
            f"- **{entry['title']}** (`{entry['id']}`, owned by {entry['owner']}): "
            f"{plain_definition(entry['definition'])}\n"
            for entry in entries
        )
        lines.append("\n")
    if changeable:
        owners = ", ".join(value.get("modules", ()))
        lines.append(
            f"The glossary {glossary} is writable, but only by entry: change, add or remove only "
            f"entries whose owner is {owners}, and never change another Module's entry or move "
            "an entry to another owner. Every other change of the file is refused after you "
            "finish.\n\n"
        )
    return "".join(lines)


def compose(prompt: str, task_type: str, value: dict) -> str:
    """The task instructions: the provider's prompt, the glossary terms of the grant and the rule
    about promises the Spec does not state."""
    return (
        prompt.strip()
        + "\n\n"
        + terms(value)
        + "## Promises the Spec does not state\n\n"
        + spec_rule(task_type)
    )


def _read(worktree: Path, path: str | None) -> bytes | None:
    if path is None:
        return None
    file = worktree / path
    return file.read_bytes() if file.is_file() and not file.is_symlink() else None


def glossary_violations(
    worktree: Path, glossary: str, before: bytes | None, modules
) -> list[str]:
    """Each glossary entry changed since ``before`` although a Module outside ``modules`` owns
    it, before or after, as ``<glossary>#<concept> (owner before: …, after: …)``."""
    from ..spec.glossary import ownership_violations

    try:
        foreign = ownership_violations(before, _read(worktree, glossary), modules)
    except (OSError, ValueError, UnicodeError) as error:
        foreign = [f"(unreadable: {error})"]
    return [f"{glossary}#{item}" for item in foreign]


def check_repair(failures: list[dict]) -> str:
    """The resume prompt naming the configured checks that failed, with the end of each log."""
    parts = [
        "The host ran the configured checks after your last round and some failed. Fix the "
        "code within your boundary and end with a new structured result.\n"
    ]
    for item in failures:
        try:
            log = Path(item["log"]).read_bytes()[-LOG_TAIL:].decode("utf-8", "replace")
        except OSError as error:
            log = f"(the log cannot be read: {error})"
        parts.append(
            f"\n## {item['check_id']} ({item['status']}, exit code {item['exit_code']})\n\n"
            f"```text\n{log}\n```\n"
        )
    return "".join(parts)


def round_validation(
    *,
    glossary: str | None,
    before: bytes | None,
    modules: list[str],
    check_modules: list[str] | None,
    validate: Callable[[dict], str | None] | None,
):
    """Method's round validation: glossary ownership, then the configured checks of
    ``check_modules`` when given, then the step's own ``validate`` of the round's worker result
    once every check passed or none ran."""
    from ..execution.checks.checks import CheckError, check_error, service_error
    from ..spec.errors import SpecError
    from .checks import run_module_checks

    def validation(worktree: Path, folder: Path, result: dict) -> RoundValidation:
        if glossary is not None:
            foreign = glossary_violations(worktree, glossary, before, modules)
            if foreign:
                return RoundValidation(
                    violation=Refusal(
                        "audit_violation",
                        f"the worker changed {len(foreign)} glossary entr"
                        f"{'y' if len(foreign) == 1 else 'ies'} that a Module outside its "
                        f"grant owns: {', '.join(foreign)}",
                    )
                )
        checks: list[dict] = []
        if check_modules is not None:
            try:
                checks = run_module_checks(
                    worktree,
                    check_modules,
                    trace_directory=layout.checks_folder(folder),
                )
            except (CheckError, SpecError, OSError) as error:
                code = getattr(error, "code", None) or "checks_unavailable"
                return RoundValidation(
                    unavailable=Refusal(
                        "checks_unavailable",
                        f"the configured checks of {', '.join(check_modules)} could not run "
                        f"({code}): {error}",
                        (service_error(error),),
                    )
                )
            failures = [item for item in checks if item["status"] != "passed"]
            if failures:
                return RoundValidation(
                    evidence=tuple(checks),
                    repair=check_repair(failures),
                    failure=Refusal(
                        "checks_failed",
                        f"{len(failures)} configured check(s) still fail: "
                        + ", ".join(item["check_id"] for item in failures),
                        tuple(check_error(item) for item in failures),
                    ),
                )
        repair = validate(result) if validate is not None else None
        return RoundValidation(evidence=tuple(checks), repair=repair or None)

    return validation


def project_interpreter(ctx: RunContext) -> str | None:
    """The project's own interpreter, as its checks run it, or None when none is configured or
    it cannot be found."""
    from ..execution.checks.checks import CheckError, project_python
    from ..spec.errors import SpecError
    from ..spec.repository import SpecRepository

    try:
        configured = SpecRepository(ctx.worktree).config.get("python")
        if not configured:
            return None
        return project_python(ctx.worktree, configured, "worker")
    except (CheckError, SpecError, OSError):
        return None


def model_failure(ctx: RunContext, worker: str, error: models.ModelConfigError) -> Stop:
    """Stop ``failed``: the backend or the worker configuration cannot be settled."""
    path = models.config_path(ctx.worktree).as_posix()
    reason = models.HANDLING.get(error.code, ("input",))[0]
    return ctx.fail(
        "failed",
        "worker_model_unavailable",
        f"The {worker} worker could not be configured ({error.code}).",
        f"the backend and model of the {worker} worker of {ctx.name} in {ctx.worktree} "
        f"cannot be settled: {error.code}: {error} (configuration file {path})",
        reason=reason,
        explanation="an Operation runs a worker on the program the worker configuration "
        "chooses for it, otherwise on pi, with the model, level and limits given there, and "
        "never guesses, repairs or falls back from any of them",
        evidence=[evidence("worker_configuration", path, f"{error.code}: {error}")],
        causes=[
            model_cause(
                error,
                "Workers reads the backend, model, level and limits from the file and "
                "changes nothing",
            )
        ],
        options=(
            [
                "write or correct this machine's model map as the error says, giving the "
                "worker's project model name its local id on the worker's backend; the map "
                "is the user's and is never committed"
            ]
            if error.code
            in ("model_map_missing", "model_map_invalid", "model_unmapped")
            else [
                (
                    "install the program the worker runs on, or edit the backend of "
                    f"operations.{ctx.name}.workers.{worker} in {path}"
                ),
                f"correct {path} as the error says and commit it; an unbound run reads the "
                "committed file of its checkout",
            ]
        ),
    )


def grant_failure(ctx: RunContext, task_type: str, modules: list[str], error) -> Stop:
    code = getattr(error, "code", None) or "grant_unavailable"
    names = ", ".join(modules)
    return ctx.fail(
        "failed",
        "grant_unavailable",
        f"The {task_type} grant for {names} could not be computed ({code}).",
        f"the {task_type} grant for {names} cannot be computed from the Specs of "
        f"{ctx.worktree}: {code}: {error}",
        reason="scope",
        explanation="an Operation computes grants from the workspace's Specs and never "
        "repairs them; the Specs or the bound Modules must change first",
        evidence=[evidence("grant", names, f"{code}: {error}")],
        causes=[spec_cause(error, "Spec core (grant)")],
        options=[
            "bind every Module that binds the shared file",
            "repair the Specs with specify or by hand",
            "run concorde task-validation for every structural finding",
        ],
    )


def run_worker(
    ctx: RunContext,
    instructions: str,
    *,
    task_type: str,
    output_schema: dict | None = None,
    checks: bool = False,
    rounds: int | None = None,
    modules: list[str] | None = None,
    worker: str | None = None,
    read_only: bool = False,
    readable: tuple[Path, ...] = (),
    validate: Callable[[dict], str | None] | None = None,
):
    """The standard worker sequence of one worker-backed step; returns ``Continue`` or ``Stop``.

    ``worker`` is the id of the worker to launch, one the provider declares; the worker
    configuration chooses its backend, model and level. ``checks`` asks the round validation to
    run the configured checks of the bound Modules and every Module that uses one of them;
    ``validate`` is the step's own validation of the round's worker result after them, answering
    the text to repair or None.

    ``read_only`` withholds every writable level of the task type's grant, turning it into read
    access, as the Protocol lets a harness give less than a type assigns. ``readable`` names host
    material outside the grant the worker may read as well, such as the logs of the checks the
    host ran for this run.
    """
    from ..spec.errors import SpecError
    from .checks import checked_modules
    from ..spec.grants import grant
    from ..spec.repository import SpecRepository

    bound = modules or ctx.modules
    worker = worker or ctx.workers[0]
    if worker not in ctx.workers:
        raise ValueError(
            f"{ctx.name} declares the workers {', '.join(ctx.workers)}, not {worker}"
        )
    if ctx.unbound and task_type in WRITING_TASK_TYPES and not read_only:
        return ctx.fail(
            "failed",
            "unbound_write",
            f"A {task_type} worker needs a bound workspace.",
            f"{ctx.name} ran unbound in a checkout of {ctx.started_in}, which has no "
            f"workspace binding, and asked for a {task_type} worker, which may change "
            "files; an unbound run launches only read-only workers",
            reason="scope",
            explanation="changing Specs or code happens only in a bound workspace, which "
            "this run does not have",
            options=[
                "run the Operation in a bound workspace, such as a task worktree "
                "(concorde task open)"
            ],
        )
    try:
        repository = SpecRepository(ctx.worktree)
        computed = grant(repository, bound, task_type).value
        check_modules = checked_modules(repository, bound) if checks else None
    except (SpecError, OSError, ValueError) as error:
        return grant_failure(ctx, task_type, bound, error)
    if read_only:
        computed = withhold_writes(computed)
        ctx.evidence.append(
            evidence(
                "grant-withheld",
                task_type,
                "every writable level of the grant was lowered to read",
            )
        )
    try:
        declared = declared_workers()
        config = models.load(ctx.worktree, declared)
        model = models.worker_choice(config, declared, ctx.name, worker)
    except models.ModelConfigError as error:
        return model_failure(ctx, worker, error)
    bounds = models.limits(config)
    readable_paths = tuple(
        Path(path) if os.path.isabs(path) else ctx.worktree / path
        for path in models.runtime(config)
        if (Path(path) if os.path.isabs(path) else ctx.worktree / path).exists()
    ) + tuple(Path(path) for path in readable if Path(path).exists())
    interpreter = project_interpreter(ctx)
    if interpreter is not None:
        # The environment the interpreter belongs to, and the installation it links to,
        # must be readable for the worker to run it; neither is ever writable.
        readable_paths += interpreter_roots(interpreter)
    glossary = (
        computed.get("glossary")
        if writable(computed["entries"], computed.get("glossary"))
        else None
    )
    before = _read(ctx.worktree, glossary)
    record = launch(
        WorkerRequest(
            worktree=ctx.worktree,
            trace_parent=ctx.run_dir,
            task_type=task_type,
            grant=grant_input(computed),
            instructions=compose(instructions, task_type, computed),
            runtime=readable_paths,
            output_schema=output_schema,
            rounds=rounds if rounds is not None else bounds["rounds"],
            timeout=float(bounds["timeout_seconds"]),
            max_turns=bounds["max_turns"],
            max_budget_usd=bounds["max_budget_usd"],
            model=model["model"],
            local_model=model["local_model"],
            model_map=model["model_map"],
            backend=model["backend"],
            backend_source=model["backend_source"],
            reasoning=model["reasoning"],
            operation=ctx.name,
            worker=worker,
            modules=tuple(computed["modules"]),
            operation_run=ctx.run_id,
            round_validation=round_validation(
                glossary=glossary,
                before=before,
                modules=list(computed["modules"]),
                check_modules=check_modules,
                validate=validate,
            ),
            project_python=interpreter,
            started=ctx.worker_started,
        )
    )
    outcome = absorb(ctx, record)
    if glossary is None:
        return outcome
    # The round validation sees only clean ok rounds; a round that ended otherwise and the
    # deletions carried out after the last validation are checked here, whatever the status.
    foreign = glossary_violations(ctx.worktree, glossary, before, computed["modules"])
    if not foreign:
        return outcome
    return ctx.fail(
        "failed",
        "audit_violation",
        f"The worker run {record['run_id']} changed glossary entries outside its grant.",
        f"the {task_type} worker run {record['run_id']} left {len(foreign)} glossary "
        f"entr{'y' if len(foreign) == 1 else 'ies'} changed that a Module outside its grant "
        f"owns: {', '.join(foreign)}",
        reason="permission",
        explanation="a worker may change only the glossary entries its bound Modules own, and "
        "an Operation never accepts or repairs a change of another Module's entry",
        evidence=[
            evidence("glossary-ownership", record["run_id"], item) for item in foreign
        ],
        host_evidence=list(outcome.evidence),
        causes=[record["error"]] if record.get("error") else [],
        options=WORKER_HANDLING["audit_violation"][2],
    )


def absorb(ctx: RunContext, record: dict):
    """Map one worker run record to a step outcome, adding host evidence."""
    from .checks import trace_writes

    ctx.worker_started(record["run_id"])
    ctx.last_record = record
    ctx.worker = record.get("worker_result")
    found = [
        evidence(
            "grant",
            record.get("grant_digest") or "",
            f"{record['task_type']} grant",
        ),
        evidence("context-identity", record.get("context_identity") or "", ""),
        evidence(
            "worker-model",
            record.get("backend") or "",
            f"{record.get('worker') or 'worker'} (backend from "
            f"{record.get('backend_source') or 'the request'}): model "
            f"{record.get('model') or 'the backend default'} as "
            f"{record.get('local_model') or 'no local id'} (model map "
            f"{record.get('model_map') or 'none'}), reasoning "
            f"{record.get('reasoning') or 'the backend default'}",
        ),
    ]
    rounds = record.get("rounds") or []
    for item in rounds:
        audit = item.get("audit")
        if audit:
            found.append(
                evidence(
                    "audit",
                    str(item["round"]),
                    f"{len(audit['changed'])} changed, violations: {', '.join(audit['violations']) or 'none'}",
                )
            )
        for check in item.get("evidence") or []:
            if "check_id" in check:
                found.append(
                    evidence(
                        "check",
                        check["check_id"],
                        f"{check['status']}, exit {check['exit_code']}; log {check['log']}",
                    )
                )
    found.append(evidence("rounds", "", f"{len(rounds)} round(s)"))
    # Tracing is best-effort for the work, never silent: each refused write of the worker run's,
    # a round's or a round's check's trace.json is the run's own evidence, whatever the step
    # makes of this outcome.
    ctx.evidence.extend(
        evidence("trace-write", record["run_id"], failure)
        for failure in record.get("trace_failures") or ()
    )
    ctx.evidence.extend(
        trace_writes(
            check
            for item in rounds
            for check in item.get("evidence") or ()
            if "check_id" in check
        )
    )
    if record.get("transcript"):
        found.append(evidence("transcript", record["transcript"], ""))
    if record.get("stderr_tail"):
        found.append(
            evidence("stderr", record["run_id"], record["stderr_tail"][-2000:])
        )
    status = record["status"]
    if status == "ok":
        return Continue(output=(ctx.worker or {}).get("output"), evidence=found)
    cause = record.get("error")
    code = cause["code"] if cause else "worker_run_failed"
    reason, explanation, options = WORKER_HANDLING.get(code, ENVIRONMENT_HANDLING)
    worker_options = [
        option for item in (cause or {}).get("causes", []) for option in item["options"]
    ]
    detail = (
        f"the {record['task_type']} worker run {record['run_id']} ended {status}: "
        f"{code}: {cause['detail'] if cause else 'the run record carries no error'}"
    )
    return ctx.fail(
        status,
        code,
        f"The worker run {record['run_id']} ended {status} ({code}).",
        detail,
        reason=reason,
        explanation=explanation,
        host_evidence=found,
        causes=[cause],
        options=worker_options + options,
    )


__all__ = [
    "WORKER_HANDLING",
    "WRITING_TASK_TYPES",
    "absorb",
    "check_worker_models",
    "compose",
    "declared_workers",
    "grant_input",
    "interpreter_roots",
    "operation",
    "round_validation",
    "run_worker",
    "runtime_paths",
    "withhold_writes",
]
