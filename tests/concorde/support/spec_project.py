"""Protocol 12 consumer fixture shared by the test suite."""

import json
from pathlib import Path

from concorde.distribution.project_defaults import install_project_defaults
from concorde.spec.initialize import apply_project_proposal, project_proposal

PACKAGE = Path(__file__).resolve().parents[3]
MIRRORED = ("owns", "contains", "uses", "includes", "participates")


class DocumentSource(str):
    """One fixture document: reading text plus its metadata, optionally with an obligations document.

    An entry's ``module`` block may leave ``owns`` as ``None``; ``write_document`` fills it with the
    entry, its obligations document and the ``extra_owned`` siblings.
    """

    metadata: dict
    implementation: "DocumentSource | None"
    extra_owned: tuple[str, ...]

    def __new__(cls, reading, metadata, implementation=None, extra_owned=()):
        value = super().__new__(cls, reading)
        value.metadata = metadata
        value.implementation = implementation
        value.extra_owned = tuple(extra_owned)
        return value


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
    file.write_text(str(source))
    if isinstance(source, DocumentSource):
        (root / (path + ".json")).write_text(
            json.dumps(complete_metadata(path, source), indent=2) + "\n"
        )
        if source.implementation is not None:
            write_document(root, obligations_path(path), source.implementation)


def source_pairs(paths):
    return sorted(member for path in paths for member in (path, path + ".json"))


def read_json(root, path):
    return json.loads((root / path).read_text())


def write_json(root, path, value):
    (root / path).write_text(json.dumps(value, indent=2) + "\n")


def registry(root) -> dict:
    return read_json(root, ".concorde/specs.json")


def entry_of(root, module_id: str) -> str:
    return next(m["entry"] for m in registry(root)["modules"] if m["id"] == module_id)


def sync_registry(root) -> dict:
    """Regenerate every record's mirrored fields (and title) from the entries."""
    value = registry(root)
    for record in value["modules"]:
        block = read_json(root, record["entry"] + ".json")["module"]
        record["title"] = block["title"]
        record.update({name: block[name] for name in MIRRORED})
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

    Every spelling of the template's short name is replaced, and the copy's concept titles are
    qualified by the new name so that no two Modules own same-named concepts.
    """
    template = next(m for m in registry(root)["modules"] if m["id"] == template_id)
    short = template_id.split(".")[-1]

    def rename(text: str) -> str:
        return text.replace(short, name).replace(short.title(), name.title())

    concepts: dict[str, str] = {}
    for path in template["owns"]:
        metadata = json.loads(rename((root / (path + ".json")).read_text()))
        for record in metadata["defines"]:
            if record["type"] == "concept":
                concepts[record["title"]] = f"{record['title']} of {name}"
                record["title"] = concepts[record["title"]]
            else:
                for entry in record["entries"]:
                    source = root / entry.replace(name, short)
                    if source.is_file() and not (root / entry).exists():
                        (root / entry).parent.mkdir(parents=True, exist_ok=True)
                        (root / entry).write_bytes(source.read_bytes())
        reading = rename((root / path).read_text())
        for old, new in concepts.items():
            reading = reading.replace(f"| {old} |", f"| {new} |").replace(
                f'["{old}"]', f'["{new}"]'
            )
        target = root / rename(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(reading)
        write_json(root, rename(path) + ".json", metadata)
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
    """A Protocol 12 Module entry and its obligations document.

    ``nodes`` is ``(design prose, [node, ...])``; each node has ``id``, ``type`` (``concept`` or
    ``realization``), ``title``, ``meaning`` (explanatory prose), and ``definition`` (concepts) or
    ``entries`` and optional ``pending`` (realizations). ``uses`` items have ``target``,
    ``explanation`` and optional ``relies_on``. ``imports`` are ``(label, href)`` pairs.
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
        "relations": [dict(item) for item in relations],
    }
    rows, prose = [], []
    for node in declared:
        record = {
            "id": node["id"],
            "type": node["type"],
            "title": node["title"],
            "meaning": "#" + node["id"],
        }
        if node["type"] == "concept":
            rows.append(f"| {node['title']} | {node['definition']} |")
        else:
            record["entries"] = list(node["entries"])
            if node.get("pending"):
                record["pending"] = list(node["pending"])
        metadata["defines"].append(record)
        prose.append(f'<a id="{node["id"]}"></a>\n\n{node["meaning"]}')
    rows.extend(f"| [{label}]({href}) | |" for label, href in imports)
    terminology = (
        "| Term | Definition |\n| --- | --- |\n" + "\n".join(rows)
        if rows
        else "This Module defines no terms of its own."
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
        f"# {title}\n\n## Purpose\n\n{purpose}\n\n## Terminology\n\n{terminology}\n\n"
        "## Usage\n\n"
        "Use the declared boundary for the cases below; rejected input has no implicit retry.\n\n"
        f"## Design\n\n{design}\n\n"
        + "".join(item + "\n\n" for item in prose)
        + f"## Relationships\n\n{architecture}\n\n"
        + (f"```mermaid\n{diagram}\n```\n\n" if diagram else "")
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
    return DocumentSource(text.rstrip("\n") + "\n", metadata, precise, extra_owned)


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
    "flowchart TB\n"
    "    accTitle: Banking coordination\n"
    "    accDescr: A transfer request is admitted by Transfers, which reads balances from the Ledger; Banking reports accepted changes to Audit.\n"
    '    bank["Banking"]\n    request["Transfer request"]\n    transfer["Transfers"]\n'
    '    ledger["Ledger"]\n    audit["Audit"]\n'
    "    request -->|admitted by| transfer\n"
    "    transfer -->|reads balances from| ledger\n"
    "    bank -->|reports accepted changes to| audit",
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
    "flowchart TB\n"
    "    accTitle: Audit outcomes\n"
    "    accDescr: One audit record describes one accepted balance change.\n"
    '    record["Audit record"]',
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
    "flowchart TB\n"
    "    accTitle: Transfer money\n"
    "    accDescr: The transfer check exercises the transfer calculation, which reads stored balances from the ledger.\n"
    '    check["Transfer check"]\n    calculation["Transfer calculation"]\n    ledger["Ledger"]\n'
    "    check -->|exercises| calculation\n"
    "    calculation -->|reads balances from| ledger",
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
    imports=[("Account", "../ledger/module.md#concept.ledger.account")],
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
    "flowchart TB\n"
    "    accTitle: Ledger API\n"
    "    accDescr: The balance store answers with the integer balance of an account or an explicit failure.\n"
    '    account["Account"]\n    store["Balance store"]\n'
    "    store -->|holds the balance of| account",
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
    """A small Protocol 12 project written from DocumentSource values, for checks tests."""

    def __init__(self, root: Path, checks=()):
        from concorde.distribution.project_defaults import write_protocol_copy
        from concorde.spec.initialize import protocol_binding

        self.root = Path(root)
        write_protocol_copy(self.root, PACKAGE)
        write_json(
            self.root,
            ".concorde/config.json",
            {
                "profile_version": 17,
                "registry": ".concorde/specs.json",
                "protocol": protocol_binding(PACKAGE),
                "checks": list(checks),
            },
        )
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

    def rules(self, severity="error"):
        return {f.rule_id for f in self.validate().findings if f.severity == severity}

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
    for path in ("specs/project/module.md", "specs/project/module.md.json"):
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
    config = read_json(root, ".concorde/config.json")
    config["checks"] = json.loads(json.dumps(CHECKS))
    write_json(root, ".concorde/config.json", config)
    return value
