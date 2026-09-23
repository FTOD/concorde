"""A three-Module Protocol 12 project in which Modules A and B both bind ``source/shared.py``."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from concorde.distribution.project_defaults import write_protocol_copy
from concorde.spec.initialize import protocol_binding
from concorde.spec.repository import SpecRepository

from .spec_project import (
    MIRRORED,
    DocumentSource,
    module_document,
    write_document,
)

PACKAGE = Path(__file__).resolve().parents[3]


def realization(identity, title, meaning, entries, pending=()):
    return {
        "id": identity,
        "type": "realization",
        "title": title,
        "meaning": meaning,
        "entries": list(entries),
        "pending": list(pending),
    }


ROOT = module_document(
    "document.root",
    "module.root",
    "Root",
    "ROOT_MODULE_CONTRACT: the root composes its two submodules and owns no code.",
    "### scenario.root.value — The root reports a composed value\n\n"
    "- GIVEN both submodules answer\n- WHEN the root is asked for its value\n"
    "- THEN it reports the composed integer\n",
    ("The root delegates both answers to its children.", []),
    "The root contains A and B, which both answer with an integer.",
    "flowchart TB\n    accTitle: root composition\n"
    "    accDescr: The root contains A and B.\n"
    '    root["Root"]\n    a["A"]\n    b["B"]\n'
    "    root -->|contains| a\n    root -->|contains| b",
    contains=[
        {
            "target": "module.a",
            "explanation": "A adapts the shared value and returns an integer.",
        },
        {
            "target": "module.b",
            "explanation": "B reads the shared value and returns 42.",
        },
    ],
)
MODULE_A = module_document(
    "document.a",
    "module.a",
    "A",
    "A_MODULE_CONTRACT: A adapts the shared integer for its own consumers.",
    "### scenario.a.value — A adapts the shared value\n\n"
    "- GIVEN the shared value function\n- WHEN A adapts it\n- THEN it returns the same integer\n"
    "- AND the shared value is unchanged\n",
    (
        "The adapter reads the shared value function.",
        [
            realization(
                "realization.a.adapter",
                "Adapter",
                "Adapts the shared integer.",
                ["source/a.py"],
            ),
            realization(
                "realization.a.shared",
                "Shared value",
                "Answers with the shared integer.",
                ["source/shared.py"],
            ),
        ],
    ),
    "The adapter reads the shared value.",
    "flowchart TB\n    accTitle: A\n"
    "    accDescr: The adapter reads the shared value function.\n"
    '    adapter["Adapter"]\n    shared["Shared value"]\n    adapter -->|reads| shared',
    requirements="### req.a.pure — A never changes the shared value\n\n"
    "A SHALL NOT change the shared value.\n",
    relations=[
        {
            "type": "relates",
            "source": "realization.a.adapter",
            "verb": "reads",
            "target": "realization.a.shared",
        }
    ],
    extra_owned=("details.md",),
)
DETAILS_A = DocumentSource(
    "# Local details\n\nA_OWN_ADDITIONAL_CONTRACT: the adapted integer is never negative.\n",
    {
        "schema_version": 3,
        "document": {"id": "document.a.details", "owner": "module.a", "role": "module"},
        "defines": [],
        "relations": [],
    },
)
MODULE_B = module_document(
    "document.b",
    "module.b",
    "B",
    "B_PRIVATE_SPEC: B reads the shared integer and promises exactly 42.",
    "### scenario.b.value — B reports the shared value\n\n"
    "- GIVEN the shared value function\n- WHEN B is asked for its value\n- THEN it returns 42\n",
    (
        "B holds only the shared value function.",
        [
            realization(
                "realization.b.shared",
                "Shared value",
                "Answers with the shared integer.",
                ["source/shared.py"],
            )
        ],
    ),
    "B collaborates with no other Module.",
)


class SharedFileProject:
    """Test-case mixin: root contains A and B; A and B both bind ``source/shared.py``."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.configuration = {
            "type_id": "concorde-operation-configuration",
            "schema_version": 2,
            "data": {"model": "openai-codex/gpt-6-astra", "thinking": "medium"},
        }
        self.write(
            ".concorde/config.json",
            json.dumps(
                {
                    "profile_version": 16,
                    "registry": ".concorde/specs.json",
                    "protocol": protocol_binding(PACKAGE),
                    "operation_configuration": self.configuration,
                    "checks": [],
                }
            ),
        )
        write_protocol_copy(self.root, PACKAGE)
        self.write(
            "source/shared.py", "def value():\n    return 42\n# PRIVATE_SOURCE_MARKER\n"
        )
        self.write("source/a.py", "def adapt(value):\n    return value\n")
        self.entries = {
            "module.root": "specs/root/module.md",
            "module.a": "specs/a/module.md",
            "module.b": "specs/b/module.md",
        }
        self.write("specs/root/module.md", ROOT)
        self.write("specs/a/module.md", MODULE_A)
        self.write("specs/a/details.md", DETAILS_A)
        self.write("specs/b/module.md", MODULE_B)
        self.registry = {"schema_version": 3, "modules": []}
        for module_id, entry in self.entries.items():
            block = json.loads((self.root / (entry + ".json")).read_text())["module"]
            self.registry["modules"].append(
                {"id": module_id, "title": block["title"], "entry": entry}
                | {name: block[name] for name in MIRRORED}
            )
        self.save_registry()

    def write(self, path, content):
        write_document(self.root, path, content)

    def save_registry(self):
        self.write(".concorde/specs.json", json.dumps(self.registry, indent=2))

    def metadata(self, module_id):
        return json.loads((self.root / (self.entries[module_id] + ".json")).read_text())

    def save_metadata(self, module_id, value):
        (self.root / (self.entries[module_id] + ".json")).write_text(
            json.dumps(value, indent=2) + "\n"
        )
        record = next(m for m in self.registry["modules"] if m["id"] == module_id)
        record.update({name: value["module"][name] for name in MIRRORED})
        self.save_registry()

    def update_module(self, module_id, **changes):
        value = self.metadata(module_id)
        value["module"].update(changes)
        self.save_metadata(module_id, value)

    def repository(self):
        return SpecRepository(self.root, PACKAGE)

    def relist(self, entries, module_id="module.a"):
        """Rewrite realization entries: ``{realization id: (entries, pending)}``."""
        value = self.metadata(module_id)
        for record in value["defines"]:
            if record["id"] in entries:
                files, pending = entries[record["id"]]
                record["entries"] = list(files)
                record["pending"] = list(pending)
        self.save_metadata(module_id, value)

    def configure_checks(self, checks):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        config["checks"] = checks
        self.write(".concorde/config.json", json.dumps(config))

    def declare_reference(self, module="module.a", entries=("reference/lib/",)):
        """Declare vendored material as ``includes`` of kind ``external`` of ``module``."""
        includes = [
            item
            for item in self.metadata(module)["module"]["includes"]
            if item["kind"] != "external"
        ] + [
            {
                "kind": "external",
                "target": entry,
                "reason": "the library's API reference",
            }
            for entry in entries
        ]
        self.update_module(module, includes=includes)


class SharedFileFixture(SharedFileProject):
    """The project as a helper object whose cleanups belong to the given test case."""

    def __init__(self, test):
        self.test = test

    def addCleanup(self, function, /, *args, **kwargs):
        self.test.addCleanup(function, *args, **kwargs)
