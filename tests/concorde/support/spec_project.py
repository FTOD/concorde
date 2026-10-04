"""Protocol 16 consumer fixture shared by the test suite."""

import json
import os
import sys
from pathlib import Path

from concorde.distribution.project_defaults import install_project_defaults
from concorde.spec.initialize import apply_project_proposal, project_proposal

PACKAGE = Path(__file__).resolve().parents[3]
MIRRORED = ("owns", "contains", "uses", "includes", "participates")
# The fixture projects' glossary, declared by their first root Module (see ``sync_registry``).
GLOSSARY = "specs/glossary.json"
# Written in a fixture document where a term link addresses the glossary; ``write_document``
# replaces it with the glossary's path relative to the document.
GLOSSARY_LINK = "@glossary"


class DocumentSource(str):
    """One fixture document: reading text plus its metadata, optionally with an obligations document.

    An entry's ``module`` block may leave ``owns`` as ``None``; ``write_document`` fills it with the
    entry, its obligations document and the ``extra_owned`` siblings. ``concepts`` are the glossary
    entries the document explains, without their ``explanation``: ``write_document`` adds it and
    upserts them into the project glossary.
    """

    metadata: dict
    implementation: "DocumentSource | None"
    extra_owned: tuple[str, ...]
    concepts: tuple[dict, ...]

    def __new__(
        cls, reading, metadata, implementation=None, extra_owned=(), concepts=()
    ):
        value = super().__new__(cls, reading)
        value.metadata = metadata
        value.implementation = implementation
        value.extra_owned = tuple(extra_owned)
        value.concepts = tuple(concepts)
        return value


def glossary_link(path: str) -> str:
    """The glossary's path relative to a document, as a term link addresses it."""
    return os.path.relpath(GLOSSARY, os.path.dirname(path))


def read_glossary(root) -> dict:
    file = Path(root) / GLOSSARY
    if not file.exists():
        return {"schema_version": 1, "concepts": []}
    return json.loads(file.read_text())


def write_glossary(root, value: dict) -> None:
    value["concepts"].sort(key=lambda entry: entry["id"])
    file = Path(root) / GLOSSARY
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(value, indent=2) + "\n")


def upsert_concepts(root, path: str, concepts) -> None:
    """Declare or replace glossary entries explained in the document at ``path``, and let the
    root Module declare the glossary."""
    _upsert(root, path, concepts)
    sync_registry(root)


def _upsert(root, path: str, concepts) -> None:
    value = read_glossary(root)
    entries = {entry["id"]: entry for entry in value["concepts"]}
    for concept in concepts:
        entry = {key: val for key, val in concept.items() if key != "anchor"}
        entry["explanation"] = f"{path}#{concept.get('anchor', concept['id'])}"
        entries[entry["id"]] = entry
    value["concepts"] = list(entries.values())
    write_glossary(root, value)


def update_glossary_entry(root, identity: str, **changes) -> dict:
    """Change fields of one glossary entry (a value of ``None`` removes the field)."""
    value = read_glossary(root)
    for entry in value["concepts"]:
        if entry["id"] == identity:
            for key, val in changes.items():
                if val is None:
                    entry.pop(key, None)
                else:
                    entry[key] = val
            write_glossary(root, value)
            return entry
    raise KeyError(identity)


def obligations_path(path: str) -> str:
    return str(Path(path).with_name("obligations.md"))


def complete_metadata(path: str, source: "DocumentSource") -> dict:
    """The metadata a DocumentSource writes at ``path``, with an entry's ``owns`` filled in."""
    metadata = json.loads(json.dumps(source.metadata))
    block = metadata.get("module")
    if block is not None and block.get("owns") is None:
        owns = [path]
        if source.implementation is not None:
            owns.append(obligations_path(path))
        owns.extend(str(Path(path).with_name(name)) for name in source.extra_owned)
        block["owns"] = owns
    return metadata


def write_document(root, path, source):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(str(source).replace(GLOSSARY_LINK, glossary_link(path)))
    if isinstance(source, DocumentSource):
        (root / (path + ".json")).write_text(
            json.dumps(complete_metadata(path, source), indent=2) + "\n"
        )
        if source.concepts:
            _upsert(root, path, source.concepts)
        if source.implementation is not None:
            write_document(root, obligations_path(path), source.implementation)


def source_pairs(paths):
    return sorted(member for path in paths for member in (path, path + ".json"))


def read_json(root, path):
    return json.loads((root / path).read_text())


def write_json(root, path, value):
    (root / path).write_text(json.dumps(value, indent=2) + "\n")


def write_checks(root, checks):
    """Replace the configured checks, given with their ``module``, by one file per Module."""
    folder = Path(root) / ".concorde/checks"
    for old in folder.glob("*") if folder.is_dir() else ():
        old.unlink()
    by_module = {}
    for check in checks:
        entry = {name: value for name, value in check.items() if name != "module"}
        by_module.setdefault(check["module"], []).append(entry)
    for module, entries in by_module.items():
        folder.mkdir(parents=True, exist_ok=True)
        write_json(folder, f"{module}.json", {"checks": entries})


def read_checks(root):
    """The configured checks as Check execution loads them, each with its ``module``, in
    configuration order."""
    from concorde.execution.checks.checks import configured_checks

    return configured_checks(Path(root))


def registry(root) -> dict:
    return read_json(root, ".concorde/specs.json")


def entry_of(root, module_id: str) -> str:
    return next(m["entry"] for m in registry(root)["modules"] if m["id"] == module_id)


def place_glossary(root) -> None:
    """Let the first Module without a parent declare the glossary, and no other Module.

    Fixtures change composition freely; the declaration follows the root so that
    ``CHK.glossary.declared`` holds whenever a glossary file exists.
    """
    records = registry(root)["modules"]
    blocks = {
        record["id"]: read_json(root, record["entry"] + ".json") for record in records
    }
    children = {
        item["target"]
        for metadata in blocks.values()
        for item in metadata["module"]["contains"]
    }
    roots = [record["id"] for record in records if record["id"] not in children]
    declarer = roots[0] if roots and (Path(root) / GLOSSARY).exists() else None
    for record in records:
        metadata = blocks[record["id"]]
        block = metadata["module"]
        wanted = GLOSSARY if record["id"] == declarer else None
        if block.get("glossary") != wanted:
            if wanted is None:
                block.pop("glossary", None)
            else:
                block["glossary"] = wanted
            write_json(root, record["entry"] + ".json", metadata)


def mirror(block: dict) -> dict:
    return {name: block[name] for name in MIRRORED} | (
        {"glossary": block["glossary"]} if "glossary" in block else {}
    )


def sync_registry(root) -> dict:
    """Place the glossary declaration, then regenerate every record's mirrored fields (and
    title) from the entries."""
    place_glossary(root)
    value = registry(root)
    for record in value["modules"]:
        block = read_json(root, record["entry"] + ".json")["module"]
        record.pop("glossary", None)
        record["title"] = block["title"]
        record.update(mirror(block))
    write_json(root, ".concorde/specs.json", value)
    return value


def register_module(root, module_id: str, entry: str) -> None:
    """Add a Module record for an entry already written, then regenerate the mirror."""
    value = registry(root)
    block = read_json(root, entry + ".json")["module"]
    value["modules"].append(
        {
            "id": module_id,
            "title": block["title"],
            "entry": entry,
            **{k: block[k] for k in MIRRORED},
        }
    )
    write_json(root, ".concorde/specs.json", value)
    sync_registry(root)


def update_module(root, module_id: str, **changes) -> dict:
    """Change fields of a Module's entry ``module`` block and keep the registry mirror in step."""
    entry = entry_of(root, module_id) + ".json"
    metadata = read_json(root, entry)
    metadata["module"].update(changes)
    write_json(root, entry, metadata)
    sync_registry(root)
    return metadata["module"]


def update_document_declaration(root, path, **updates):
    document = root / (path + ".json")
    value = json.loads(document.read_text())
    value["document"].update(updates)
    document.write_text(json.dumps(value, indent=2) + "\n")


def update_defines(root, path, update):
    metadata = read_json(root, path + ".json")
    metadata["defines"] = update(metadata["defines"])
    write_json(root, path + ".json", metadata)


def set_realization(root, realization_id: str, **fields) -> None:
    """Change a realization record wherever it is declared."""
    for record in registry(root)["modules"]:
        for path in record["owns"]:
            metadata = read_json(root, path + ".json")
            for item in metadata["defines"]:
                if item["id"] == realization_id:
                    item.update(fields)
                    write_json(root, path + ".json", metadata)
                    return
    raise KeyError(realization_id)


def clone_module(root, template_id: str, name: str, **changes) -> str:
    """Copy a Module's documents and bound files under a new short name and register the copy.

    Every spelling of the template's short name is replaced, and the copy's glossary entries are
    declared with qualified titles, so that no two concepts share a title.
    """
    template = next(m for m in registry(root)["modules"] if m["id"] == template_id)
    short = template_id.split(".")[-1]

    def rename(text: str) -> str:
        return text.replace(short, name).replace(short.title(), name.title())

    for path in template["owns"]:
        metadata = json.loads(rename((root / (path + ".json")).read_text()))
        metadata.get("module", {}).pop("glossary", None)
        for record in metadata["defines"]:
            for entry in record["entries"]:
                source = root / entry.replace(name, short)
                if source.is_file() and not (root / entry).exists():
                    (root / entry).parent.mkdir(parents=True, exist_ok=True)
                    (root / entry).write_bytes(source.read_bytes())
        reading = rename((root / path).read_text())
        target = root / rename(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(reading)
        write_json(root, rename(path) + ".json", metadata)
    glossary = read_glossary(root)
    for entry in list(glossary["concepts"]):
        if entry["owner"] == template_id:
            copy = json.loads(rename(json.dumps(entry)))
            copy["title"] = f"{entry['title']} of {name}"
            glossary["concepts"].append(copy)
    if glossary["concepts"]:
        write_glossary(root, glossary)
    module_id = rename(template_id)
    register_module(root, module_id, rename(template["entry"]))
    if changes:
        update_module(root, module_id, **changes)
    return module_id


def add_consumers(root, count: int) -> list[str]:
    """Ledger-like Modules that each include the transfer promises: extra Spec consumers."""
    return [
        clone_module(
            root,
            "module.ledger",
            f"consumer{index}",
            includes=[
                {
                    "kind": "document",
                    "target": "document.transfer.promises",
                    "reason": "the transfer amount rules",
                }
            ],
        )
        for index in range(count)
    ]


def include_external(
    root, module_id: str, entry: str, reason: str = "the library API"
) -> None:
    """Declare vendored material as an ``includes`` of kind ``external`` of a Module."""
    block = read_json(root, entry_of(root, module_id) + ".json")["module"]
    update_module(
        root,
        module_id,
        includes=[
            *block["includes"],
            {"kind": "external", "target": entry, "reason": reason},
        ],
    )


def block(name, value):
    return "```" + name + "\n" + json.dumps(value, indent=2) + "\n```\n"


def module_document(
    document_id,
    target_id,
    title,
    purpose,
    scenarios,
    nodes,
    architecture,
    diagram=None,
    uses=(),
    trailer="",
    requirements="No Module-wide requirement is stated here.",
    relations=(),
    imports=(),
    contains=(),
    includes=(),
    participates=(),
    extra_owned=(),
    contracts="",
):
    """A Protocol 16 Module entry and its obligations document.

    ``nodes`` is ``(design prose, [node, ...])``; each node has ``id``, ``type`` (``concept`` or
    ``realization``), ``title``, ``meaning`` (explanatory prose), and ``definition`` (concepts) or
    ``entries`` (realizations). A concept becomes a glossary entry owned by the Module, explained
    at its anchor, whose prose links it; a ``relations`` item whose source is a concept moves into
    that entry. ``uses`` items have ``target``, ``explanation`` and optional ``relies_on``.
    ``imports`` are ``(label, concept identity)`` pairs: the Usage section links each such term.
    """
    design, declared = nodes
    metadata = {
        "schema_version": 3,
        "document": {"id": document_id, "owner": target_id, "role": "module"},
        "module": {
            "title": title,
            "owns": None,
            "contains": [],
            "uses": [],
            "includes": list(includes),
            "participates": [],
        },
        "defines": [],
        "relations": [],
    }
    prose, concepts = [], {}
    for node in declared:
        if node["type"] == "concept":
            concepts[node["id"]] = {
                "id": node["id"],
                "title": node["title"],
                "owner": target_id,
                "definition": node["definition"],
                "anchor": node["id"],
            }
            prose.append(
                f'<a id="{node["id"]}"></a>\n\n'
                f"[{node['title']}]({GLOSSARY_LINK}#{node['id']}): {node['meaning']}"
            )
            continue
        record = {
            "id": node["id"],
            "type": node["type"],
            "title": node["title"],
            "meaning": "#" + node["id"],
            "entries": list(node["entries"]),
        }
        metadata["defines"].append(record)
        prose.append(f'<a id="{node["id"]}"></a>\n\n{node["meaning"]}')
    for item in relations:
        relation = dict(item)
        concept = concepts.get(relation["source"])
        if concept is None:
            metadata["relations"].append(relation)
            continue
        kind = relation.pop("type")
        relation.pop("source")
        if kind in {"narrows"}:
            concept.setdefault("narrows", []).append(relation["target"])
        elif kind == "supersedes":
            concept["supersedes"] = relation["target"]
        else:
            concept.setdefault(kind, []).append(relation)
    terms = (
        "It uses the terms "
        + ", ".join(
            f"[{label}]({GLOSSARY_LINK}#{identity})" for label, identity in imports
        )
        + ".\n\n"
        if imports
        else ""
    )
    collaborations = []
    for kind, items in (("contains", contains), ("uses", uses)):
        for item in items:
            anchor = f"{kind}-{item['target'].replace('.', '-')}"
            relation = {"target": item["target"], "meaning": "#" + anchor}
            if item.get("relies_on"):
                relation["relies_on"] = list(item["relies_on"])
            metadata["module"][kind].append(relation)
            collaborations.append(f'<a id="{anchor}"></a>\n\n{item["explanation"]}')
    for index, item in enumerate(participates):
        anchor = f"participates-{index}"
        metadata["module"]["participates"].append(
            {key: item[key] for key in ("contract", "version", "role", "peer")}
            | {"meaning": "#" + anchor}
        )
        collaborations.append(f'<a id="{anchor}"></a>\n\n{item["explanation"]}')
    text = (
        f"# {title}\n\n## Purpose\n\n{purpose}\n\n"
        "## Usage\n\n"
        "Use the declared boundary for the cases below. Rejected input has no implicit retry.\n\n"
        f"{terms}"
        f"## Design\n\n{design}\n\n{architecture}\n\n"
        + (f"```d2\n{diagram}\n```\n\n" if diagram else "")
        + "".join(item + "\n\n" for item in prose)
        + "".join(item + "\n\n" for item in collaborations)
    )
    precise = DocumentSource(
        f"# {title} obligations\n\n## Requirements\n\n{requirements}\n\n"
        f"## Scenarios\n\n{scenarios}\n" + contracts + trailer,
        {
            "schema_version": 3,
            "document": {
                "id": document_id + ".obligations",
                "owner": target_id,
                "role": "implementation",
            },
            "defines": [],
            "relations": [],
        },
    )
    return DocumentSource(
        text.rstrip("\n") + "\n",
        metadata,
        precise,
        extra_owned,
        tuple(concepts.values()),
    )


def uses(target, explanation=None, relies_on=None):
    return {
        "target": target,
        "explanation": explanation
        or f"Relies on the {target} responsibility for the work this Module coordinates. "
        "A failure of the provider is reported, never retried silently.",
        **({"relies_on": relies_on} if relies_on else {}),
    }


# Kept for callers that describe a collaboration by its provider.
def promise(peer):
    return uses(peer)


BANK = module_document(
    "document.bank",
    "scope.bank",
    "Banking",
    "Banking coordinates money movement between customer accounts. It performs no calculation of\n"
    "its own: transfer admission and execution belong to the transfer Module, stored balances to\n"
    "the ledger Module, and audit outcomes to the audit Module.",
    "### scenario.bank.settlement — A completed transfer settles both accounts\n\n"
    "- GIVEN a sender account whose balance covers the requested amount\n"
    "- WHEN Banking accepts one transfer request\n"
    "- THEN the sender is debited and the receiver is credited\n"
    "- AND the audit Module receives the accepted balance change\n"
    "- AND a repeated request is treated as a new decision\n",
    (
        "Banking owns the request concept; the transfer, ledger and audit Modules do the work.",
        [
            {
                "id": "concept.bank.request",
                "type": "concept",
                "title": "Transfer request",
                "definition": "The sender, the receiver and the amount of one requested money movement.",
                "meaning": "Carries the sender, the receiver and the requested amount.",
            }
        ],
    ),
    "A transfer request is admitted by the transfer Module, which reads balances from the ledger\n"
    "Module. Banking reports each accepted change to the audit Module.",
    "bank: Banking\nrequest: Transfer request\ntransfer: Transfers\nledger: Ledger\naudit: Audit\n"
    "request -> transfer: admitted by\n"
    "transfer -> ledger\n"
    "bank -> audit",
    [uses(peer) for peer in ("service.transfer", "module.ledger", "scope.audit")],
    requirements="### req.bank.retry — Repeated requests are new decisions\n\n"
    "Banking SHALL treat a repeated request as a new decision.\n",
    relations=[
        {
            "type": "relates",
            "source": "concept.bank.request",
            "verb": "admitted by",
            "target": "service.transfer",
        }
    ],
)

AUDIT = module_document(
    "document.audit",
    "scope.audit",
    "Audit",
    "Audit describes the outcome an accepted balance change must produce. It owns no transfer\n"
    "calculation and no stored balance of its own.",
    "### scenario.audit.record — An accepted transfer becomes one audit record\n\n"
    "- GIVEN a transfer the transfer Module reports as successful\n"
    "- WHEN Audit receives that accepted balance change\n"
    "- THEN one audit record describes the sender, the receiver and the amount\n",
    (
        "Audit owns its record concept and observes the transfer Module.",
        [
            {
                "id": "concept.audit.record",
                "type": "concept",
                "title": "Audit record",
                "definition": "The description of one accepted balance change.",
                "meaning": "Describes one accepted balance change.",
            }
        ],
    ),
    "Audit collaborates with no other Module; the accepted change reaches it from Banking.",
    "record: Audit record",
)

TRANSFER = module_document(
    "document.transfer.feature",
    "service.transfer",
    "Transfers",
    "The transfer Module admits one money movement and computes its result. Calls are pure: the\n"
    "Module reads stored balances through the ledger Module and stores nothing itself.",
    "### scenario.transfer.debit — A valid amount debits the sender\n\n"
    "- GIVEN a sender balance of 100\n"
    "- WHEN transfer(100, 20) is called\n"
    "- THEN it returns 80\n"
    "- AND no stored balance changes\n\n"
    "### scenario.transfer.reject — An unaffordable or non-positive amount is rejected\n\n"
    "- GIVEN a sender balance of 10\n"
    "- WHEN transfer(10, 20) is called\n"
    "- THEN it raises ValueError\n"
    "- AND no balance changes\n",
    (
        "The calculation and its executable check are the Module's own code; the ledger Module\n"
        "supplies stored balances.",
        [
            {
                "id": "realization.transfer.calculation",
                "type": "realization",
                "title": "Transfer calculation",
                "meaning": "Computes the remaining balance, or rejects the requested amount.",
                "entries": ["app/transfer.py"],
            },
            {
                "id": "realization.transfer.check",
                "type": "realization",
                "title": "Transfer check",
                "meaning": "Exercises one accepted amount and every rejected amount.",
                "entries": ["checks/transfer_check.py"],
            },
        ],
    ),
    "The check exercises the calculation, which reads stored balances from the ledger Module.\n"
    "Ledger API tasks are separately bound to that Module.",
    "check: Transfer check\ncalculation: Transfer calculation\nledger: Ledger\n"
    "check -> calculation: exercises\n"
    "calculation -> ledger: reads balances from",
    [uses("module.ledger")],
    requirements="### req.transfer.pure — Transfers store nothing\n\n"
    "transfer SHALL NOT alter any stored balance.\n",
    relations=[
        {
            "type": "relates",
            "source": "realization.transfer.check",
            "verb": "exercises",
            "target": "realization.transfer.calculation",
        },
        {
            "type": "relates",
            "source": "realization.transfer.calculation",
            "verb": "reads balances from",
            "target": "module.ledger",
        },
    ],
    imports=[("Account", "concept.ledger.account")],
    extra_owned=("promises.md",),
)

LEDGER = module_document(
    "document.ledger.api",
    "module.ledger",
    "Ledger",
    "The ledger Module stores account balances and answers one read per account identity.",
    "### scenario.ledger.read — A stored account returns its balance\n\n"
    "- GIVEN an account with a stored balance\n"
    "- WHEN read(account_id) is called\n"
    "- THEN it returns that integer balance\n\n"
    "### scenario.ledger.unknown — An unknown identity is an explicit failure\n\n"
    "- GIVEN no stored balance for the requested identity\n"
    "- WHEN read(account_id) is called\n"
    "- THEN it raises KeyError\n",
    (
        "Accounts map to integer balances held by the balance store.",
        [
            {
                "id": "concept.ledger.account",
                "type": "concept",
                "title": "Account",
                "definition": "The identity of exactly one stored balance.",
                "meaning": "Identifies exactly one stored balance.",
            },
            {
                "id": "realization.ledger.store",
                "type": "realization",
                "title": "Balance store",
                "meaning": "Maps account identities to integer balances and rejects unknown ones.",
                "entries": ["app/ledger.py"],
            },
        ],
    ),
    "An account identity indexes the balance store. Unknown identity is an explicit lookup failure.",
    "account: Account\nstore: Balance store\nstore -> account: holds the balance of",
    relations=[
        {
            "type": "relates",
            "source": "realization.ledger.store",
            "verb": "holds the balance of",
            "target": "concept.ledger.account",
        }
    ],
)

PROMISES = DocumentSource(
    "# Local promises\n\nBalance and amount are integers. No network, persistence or implicit\n"
    "retry is performed by transfer. This complete collection defines all facts required to\n"
    "implement and test transfer.\n",
    {
        "schema_version": 3,
        "document": {
            "id": "document.transfer.promises",
            "owner": "service.transfer",
            "role": "module",
        },
        "defines": [],
        "relations": [],
    },
)

# Files the git-based fixtures commit next to the Spec: the Workspace Module binds them so that
# every version-controlled file is bound (CHK.binds.unbound).
WORKSPACE = module_document(
    "document.workspace",
    "module.workspace",
    "Workspace",
    "The Workspace Module holds the project files that belong to no business responsibility: the\n"
    "project policy, a shared text file and a private script no task may read.",
    "",
    (
        "The project files are kept apart from the business Modules.",
        [
            {
                "id": "realization.workspace.files",
                "type": "realization",
                "title": "Project files",
                "meaning": "The project policy, the shared text and the private script.",
                "entries": [".gitignore", "AGENTS.md", "secret.py", "shared.txt"],
            }
        ],
    ),
    "The Workspace Module collaborates with no other Module.",
)


class SpecProject:
    """A small Protocol 16 project written from DocumentSource values, for checks tests."""

    def __init__(self, root: Path, checks=()):
        from concorde.distribution.project_defaults import write_protocol_copy
        from concorde.spec.initialize import protocol_binding

        self.root = Path(root)
        write_protocol_copy(self.root, PACKAGE)
        write_json(
            self.root,
            ".concorde/config.json",
            {
                "profile_version": 19,
                "protocol": protocol_binding(PACKAGE),
                "python": sys.executable,
            },
        )
        write_checks(self.root, checks)
        write_json(
            self.root, ".concorde/specs.json", {"schema_version": 3, "modules": []}
        )

    def write(self, path, content):
        write_document(self.root, path, content)

    def module(self, module_id, entry, source):
        """Write a Module's entry (and obligations) and register it."""
        self.write(entry, source)
        register_module(self.root, module_id, entry)

    def update(self, module_id, **changes):
        return update_module(self.root, module_id, **changes)

    def metadata(self, path):
        return read_json(self.root, path + ".json")

    def save_metadata(self, path, value):
        write_json(self.root, path + ".json", value)

    def repository(self, **options):
        from concorde.spec.repository import SpecRepository

        return SpecRepository(self.root, PACKAGE, **options)

    def validate(self):
        from concorde.spec.validation import validate_repository

        return validate_repository(self.root, package_root=PACKAGE)

    def rules(self, strictness="error"):
        return {
            f.rule_id for f in self.validate().findings if f.strictness == strictness
        }

    def findings(self, rule):
        return [f for f in self.validate().findings if f.rule_id == rule]


MODULES = (
    ("scope.bank", "specs/bank/module.md", BANK),
    ("scope.audit", "specs/audit/module.md", AUDIT),
    ("service.transfer", "specs/transfer/module.md", TRANSFER),
    ("module.ledger", "specs/ledger/module.md", LEDGER),
    ("module.workspace", "specs/workspace/module.md", WORKSPACE),
)
CHECKS = [
    {
        "id": "check.transfer",
        "module": "service.transfer",
        "argv": ["{python}", "checks/transfer_check.py"],
        "timeout_seconds": 10,
    }
]


def project(root):
    """The bank fixture: four business Modules and a Workspace Module, installed and valid."""
    install_project_defaults(
        root, PACKAGE
    )  # what the installer places before initialization
    apply_project_proposal(
        root,
        PACKAGE,
        project_proposal(root, PACKAGE, "Bank", "scope.bank"),
    )
    for path in (
        "specs/project/module.md",
        "specs/project/module.md.json",
        "specs/project/glossary.json",
    ):
        (root / path).unlink()
    (root / "specs/project").rmdir()
    files = {
        "specs/transfer/promises.md": PROMISES,
        "app/transfer.py": "# TRANSFER_IMPLEMENTATION_CODE\ndef transfer(balance, amount):\n    return balance\n",
        "app/ledger.py": "# LEDGER_IMPLEMENTATION_CODE\ndef read(account_id):\n    raise KeyError(account_id)\n",
        "checks/transfer_check.py": 'import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path.cwd()))\nfrom app.transfer import transfer\nassert transfer(100,20)==80\nfor balance,amount in [(10,20),(10,0),(10,-1)]:\n    try: transfer(balance,amount)\n    except ValueError: pass\n    else: raise AssertionError("invalid transfer accepted")\n',
        "secret.py": "PRIVATE_CODE_MUST_NOT_ENTER_SPEC_CONTEXT = True\n",
        "AGENTS.md": "# Project policy\n",
        ".gitignore": "",
        "shared.txt": "base\n",
    }
    records = []
    for module_id, path, source in MODULES:
        write_document(root, path, source)
        block = complete_metadata(path, source)["module"]
        records.append(
            {
                "id": module_id,
                "title": block["title"],
                "entry": path,
                **{k: block[k] for k in MIRRORED},
            }
        )
    for path, content in files.items():
        # Keep an installer's AGENTS.md and a project's own ignore file; bind them either way.
        if path in {"AGENTS.md", ".gitignore"} and (root / path).exists():
            continue
        write_document(root, path, content)
    value = {"schema_version": 3, "modules": records}
    write_json(root, ".concorde/specs.json", value)
    value = sync_registry(root)
    write_checks(root, CHECKS)
    return value
