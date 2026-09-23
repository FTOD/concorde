"""Every family of Protocol 11 structural checks, each on a small fixture project."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.spec.registry import registry_command
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    DocumentSource,
    SpecProject,
    block,
    module_document,
    read_json,
    sync_registry,
    write_json,
)

PROVIDER = module_document(
    "document.provider.module",
    "module.provider",
    "Provider",
    "The provider stores things and answers reads.",
    "### scenario.provider.read — A stored thing is returned\n\n"
    "- GIVEN a stored thing\n- WHEN it is read\n- THEN it is returned\n",
    (
        "The store holds things.",
        [
            {
                "id": "concept.provider.thing",
                "type": "concept",
                "title": "Thing",
                "definition": "One stored value with an identity.",
                "meaning": "A thing is what the provider stores.",
            },
            {
                "id": "realization.provider.store",
                "type": "realization",
                "title": "Store",
                "meaning": "Keeps every thing by its identity.",
                "entries": ["src/provider.py"],
            },
        ],
    ),
    "The store holds every thing.",
    'flowchart LR\n    store["Store"] -->|holds| thing["Thing"]',
    requirements="### req.provider.keep — Things are kept\n\nThe provider SHALL keep every stored thing.\n",
    relations=[
        {
            "type": "relates",
            "source": "realization.provider.store",
            "verb": "holds",
            "target": "concept.provider.thing",
        }
    ],
)
CONSUMER = module_document(
    "document.consumer.module",
    "module.consumer",
    "Consumer",
    "The consumer shows things to people.",
    "### scenario.consumer.show — A thing is shown\n\n"
    "- GIVEN a stored thing\n- WHEN a person asks for it\n- THEN it is shown\n",
    (
        "The view shows things.",
        [
            {
                "id": "realization.consumer.view",
                "type": "realization",
                "title": "View",
                "meaning": "Renders one thing.",
                "entries": ["src/consumer.py"],
            }
        ],
    ),
    "The view reads things from the provider.",
    'flowchart LR\n    view["View"] -->|shows| thing["Provider / Thing"]\n'
    '    consumer["Consumer"] -->|reads things from| provider["Provider"]',
    uses=[
        {
            "target": "module.provider",
            "explanation": "The provider keeps every [thing](../provider/module.md#concept.provider.thing); "
            "a failed read is shown as unavailable.",
        }
    ],
    relations=[
        {
            "type": "relates",
            "source": "realization.consumer.view",
            "verb": "shows",
            "target": "concept.provider.thing",
        }
    ],
    imports=[("Thing", "../provider/module.md#concept.provider.thing")],
)
ROOT = module_document(
    "document.app.module",
    "module.app",
    "App",
    "The app shows stored things.",
    "",
    ("The app is the composition of its two children.", []),
    "The app contains the provider and the consumer.",
    'flowchart TB\n    app["App"] -->|contains| provider["Provider"]\n    app -->|contains| consumer["Consumer"]',
    contains=[
        {
            "target": "module.provider",
            "explanation": "The provider stores things for the app.",
        },
        {
            "target": "module.consumer",
            "explanation": "The consumer shows the app's things.",
        },
    ],
)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.project = SpecProject(self.root)
        self.project.write("src/provider.py", "THINGS = {}\n")
        self.project.write("src/consumer.py", "def show(thing):\n    return thing\n")
        self.project.module("module.app", "specs/app/module.md", ROOT)
        self.project.module("module.provider", "specs/provider/module.md", PROVIDER)
        self.project.module("module.consumer", "specs/consumer/module.md", CONSUMER)

    def rules(self, severity="error"):
        return self.project.rules(severity)

    def entry(self, module):
        return f"specs/{module}/module.md"

    def edit(self, path, old, new):
        file = self.root / path
        text = file.read_text()
        self.assertIn(old, text)
        file.write_text(text.replace(old, new))

    def metadata(self, module, update):
        value = self.project.metadata(self.entry(module))
        update(value)
        self.project.save_metadata(self.entry(module), value)
        sync_registry(self.root)

    def relation(self, module, record):
        self.metadata(module, lambda value: value["relations"].append(record))

    @verifies(
        "scenario.spec.validate-success",
        "scenario.spec.reader-parts",
        "scenario.spec.admit-inventory",
    )
    def test_the_fixture_conforms(self):
        report = self.project.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertEqual({"CONCORDE-COVERAGE-001"}, self.rules("warning"))
        repository = self.project.repository()
        self.assertEqual(
            ({"target": "module.provider", "meaning": "#uses-module-provider"},),
            repository.module_declaration("module.consumer").uses,
        )
        self.assertEqual("module.app", repository.root_module)
        self.assertEqual(
            [
                {
                    "document": "specs/consumer/module.md",
                    "module": "module.consumer",
                    "relation": "imports",
                },
                {
                    "document": "specs/consumer/module.md",
                    "module": "module.consumer",
                    "relation": "relates",
                },
                {
                    "document": "specs/provider/module.md",
                    "module": "module.provider",
                    "relation": "relates",
                },
            ],
            list(repository.referenced_by("concept.provider.thing")),
        )

    @verifies("scenario.spec.reader-parts-invalid")
    def test_entry_sections_and_prose(self):
        entry = self.entry("consumer")
        original = (self.root / entry).read_text()
        cases = {
            "missing": original.replace("## Design\n", "## Drawing\n"),
            "misordered": original.replace("## Usage", "## Tmp")
            .replace("## Design", "## Usage")
            .replace("## Tmp", "## Design"),
            "repeated": original + "\n## Purpose\n\nAgain.\n",
            "level": original.replace("## Relationships", "### Relationships"),
            "fenced": original.replace("## Usage", "```text\n## Usage\n```"),
        }
        for label, text in cases.items():
            with self.subTest(label):
                (self.root / entry).write_text(text)
                self.assertIn("CHK.document.sections", self.rules())
        for label, text in {
            "purpose list": original.replace(
                "The consumer shows things to people.", "- The consumer shows things."
            ),
            "usage only links": original.replace(
                "Use the declared boundary for the cases below; rejected input has no implicit retry.",
                "[Provider](../provider/module.md)",
            ),
        }.items():
            with self.subTest(label):
                (self.root / entry).write_text(text)
                self.assertIn("CHK.document.prose", self.rules())
        (self.root / entry).write_text(
            original.replace("## Purpose\n", "## Purpose ##\n").rstrip()
        )
        self.assertNotIn("CHK.document.sections", self.rules())

    @verifies("scenario.spec.reader-parts")
    def test_a_topic_that_defines_a_concept_starts_with_terminology(self):
        topic = DocumentSource(
            "# Rules\n\nHow things are named.\n\n## Naming\n\nNames are short.\n\n"
            "## Terminology\n\n| Term | Definition |\n| --- | --- |\n| Name | The label of a thing. |\n\n"
            '<a id="concept.provider.name"></a>\n\nA name labels one thing.\n',
            {
                "schema_version": 3,
                "document": {
                    "id": "document.provider.rules",
                    "owner": "module.provider",
                    "role": "module",
                },
                "defines": [
                    {
                        "id": "concept.provider.name",
                        "type": "concept",
                        "title": "Name",
                        "meaning": "#concept.provider.name",
                    }
                ],
                "relations": [],
            },
        )
        self.project.write("specs/provider/rules.md", topic)
        self.metadata(
            "provider",
            lambda value: value["module"]["owns"].append("specs/provider/rules.md"),
        )
        self.assertIn("CHK.document.topic-terminology", self.rules())
        self.edit(
            "specs/provider/rules.md",
            "## Naming\n\nNames are short.\n\n## Terminology",
            "## Terminology",
        )
        self.edit(
            "specs/provider/rules.md",
            "| Name | The label of a thing. |\n",
            "| Name | The label of a thing. |\n\n## Naming\n\nNames are short.\n",
        )
        self.assertEqual(
            set(),
            self.rules() & {"CHK.document.topic-terminology", "CHK.concept.definition"},
        )

    @verifies("scenario.spec.node-checks")
    def test_node_meaning_definition_contract_and_explanation(self):
        self.edit(
            self.entry("provider"),
            "| Thing | One stored value with an identity. |\n",
            "",
        )
        self.assertIn("CHK.concept.definition", self.rules())
        self.edit(
            self.entry("provider"),
            "| Term | Definition |\n| --- | --- |\n",
            "| Term | Definition |\n| --- | --- |\n| Thing | One value. It has an identity. |\n",
        )
        self.assertIn("CHK.concept.definition", self.rules())
        self.edit(
            self.entry("provider"),
            '<a id="concept.provider.thing"></a>',
            '<a id="concept.provider.other"></a>',
        )
        rules = self.rules()
        self.assertIn("CHK.node.meaning", rules)
        contract = {
            "id": "contract.provider.read",
            "version": 1,
            "schema": {"type": "integer"},
            "semantics": "The stored count.",
            "example": "not an integer",
        }
        with (self.root / "specs/provider/obligations.md").open("a") as stream:
            stream.write("\n## Contracts\n\n" + block("concorde-contract", contract))
        self.assertIn("CHK.contract.fence", self.rules())
        self.edit(
            self.entry("consumer"),
            "Renders one thing.",
            "[Provider](../provider/module.md)",
        )
        self.assertIn("CHK.node.explained", self.rules("warning"))

    @verifies("scenario.spec.terminology-imports")
    def test_terminology_rows_and_imports(self):
        report = self.project.validate()
        self.assertEqual("success", report.status)
        entry = self.entry("consumer")
        original = (self.root / entry).read_text()
        cases = {
            "CHK.terminology.import-row": original.replace(
                "| [Thing](../provider/module.md#concept.provider.thing) | |",
                "| [Thing](../provider/module.md#concept.provider.thing) | A copied definition. |",
            ),
            "CHK.terminology.rows": original.replace(
                "| [Thing](../provider/module.md#concept.provider.thing) | |",
                "| [Thing](../provider/module.md#concept.provider.thing) | |\n| Widget | Not declared. |",
            ),
        }
        for rule, text in cases.items():
            with self.subTest(rule):
                (self.root / entry).write_text(text)
                self.assertIn(rule, self.rules())
        (self.root / entry).write_text(original)
        self.edit(
            self.entry("provider"),
            "| Thing | One stored value with an identity. |",
            "| Thing | One stored value with an identity. |\n| [Thing](module.md#concept.provider.thing) | |",
        )
        self.assertIn("CHK.terminology.import-row", self.rules())

    @verifies("scenario.spec.terminology-imports", "scenario.spec.context-reconciled")
    def test_imports_need_a_provider_in_context_and_an_owner_used_or_related(self):
        # The provider stops being used: its concept is imported from an unrelated Module.
        self.metadata("consumer", lambda value: value["module"].update(uses=[]))
        self.edit(
            self.entry("consumer"),
            '    consumer["Consumer"] -->|reads things from| provider["Provider"]',
            "",
        )
        rules = self.rules()
        self.assertIn("CHK.context.reconciled", rules)
        self.assertIn("CHK.imports.owner", self.rules("warning"))
        # An include with a reason repairs the context requirement.
        self.metadata(
            "consumer",
            lambda value: value["module"]["includes"].append(
                {
                    "kind": "document",
                    "target": "document.provider.module",
                    "reason": "the Thing definition",
                }
            ),
        )
        self.assertNotIn("CHK.context.reconciled", self.rules())
        # A parent importing its child's term is fine.
        self.edit(
            self.entry("app"),
            "This Module defines no terms of its own.",
            "| Term | Definition |\n| --- | --- |\n| [Thing](../provider/module.md#concept.provider.thing) | |",
        )
        self.assertNotIn(
            "specs/app/module.md",
            [f.source for f in self.project.findings("CHK.imports.owner")],
        )

    @verifies("scenario.spec.composition-checks")
    def test_composition_and_dependency_rules(self):
        self.metadata(
            "consumer",
            lambda value: value["module"]["uses"].append(
                dict(value["module"]["uses"][0])
            ),
        )
        self.assertIn("CHK.uses.unique", self.rules())
        self.metadata(
            "consumer",
            lambda value: value["module"].update(
                uses=[
                    value["module"]["uses"][0],
                    {"target": "module.consumer", "meaning": "#uses-module-provider"},
                ]
            ),
        )
        self.assertIn("CHK.uses.no-self", self.rules())
        self.metadata(
            "consumer",
            lambda value: value["module"].update(uses=value["module"]["uses"][:1]),
        )
        # Mutual uses are legitimate.
        self.metadata(
            "provider",
            lambda value: value["module"]["uses"].append(
                {"target": "module.consumer", "meaning": "#holds"}
            ),
        )
        self.edit(
            self.entry("provider"),
            "The store holds every thing.",
            '<a id="holds"></a>\n\nThe provider notifies the consumer.',
        )
        self.assertEqual(
            set(),
            self.rules()
            & {"CHK.uses.no-self", "CHK.uses.unique", "CHK.contains.acyclic"},
        )
        # A second parent, then a cycle.
        self.metadata(
            "consumer",
            lambda value: value["module"]["contains"].append(
                {"target": "module.provider", "meaning": "#uses-module-provider"}
            ),
        )
        with self.assertRaisesRegex(SpecError, "CHK.contains.single-parent"):
            self.project.repository()
        self.assertIn("CHK.contains.single-parent", self.rules())
        self.metadata("consumer", lambda value: value["module"].update(contains=[]))
        self.metadata(
            "provider",
            lambda value: value["module"]["contains"].append(
                {"target": "module.app", "meaning": "#holds"}
            ),
        )
        with self.assertRaisesRegex(SpecError, "cycle"):
            self.project.repository()
        self.assertIn("CHK.contains.acyclic", self.rules())

    @verifies("scenario.spec.composition-checks")
    def test_more_than_one_root_is_a_warning(self):
        self.metadata(
            "app",
            lambda value: value["module"].update(
                contains=value["module"]["contains"][:1]
            ),
        )
        self.edit(self.entry("app"), '    app -->|contains| consumer["Consumer"]', "")
        self.assertIn("CHK.contains.root", self.rules("warning"))
        self.assertNotIn("CHK.contains.root", self.rules())

    @verifies("scenario.spec.relies-on")
    def test_relies_on_names_owned_nodes_and_every_linked_one(self):
        def narrow(ids):
            self.metadata(
                "consumer",
                lambda value: value["module"]["uses"][0].update(relies_on=ids),
            )

        narrow(["concept.provider.thing", "req.provider.keep"])
        self.assertEqual(
            set(), self.rules() & {"CHK.relies-on.owned", "CHK.relies-on.linked"}
        )
        narrow(["req.provider.keep"])
        self.assertIn("CHK.relies-on.linked", self.rules())
        narrow(["concept.provider.thing", "realization.provider.store"])
        self.assertIn("CHK.relies-on.owned", self.rules())
        narrow(["concept.provider.thing", "scenario.consumer.show"])
        self.assertIn("CHK.relies-on.owned", self.rules())

    @verifies("scenario.spec.reference-invalid")
    def test_relation_targets_and_includes(self):
        include = {"kind": "module", "target": "module.provider", "reason": "the store"}
        self.metadata(
            "consumer", lambda value: value["module"]["includes"].append(include)
        )
        self.assertIn("CHK.includes.redundant", self.rules("warning"))
        self.metadata(
            "consumer", lambda value: value["module"]["includes"].append(dict(include))
        )
        self.assertIn("CHK.includes.unique", self.rules())
        self.metadata(
            "consumer",
            lambda value: value["module"].update(
                includes=[
                    {
                        "kind": "document",
                        "target": "document.consumer.module",
                        "reason": "self",
                    }
                ]
            ),
        )
        self.assertIn("CHK.includes.no-self", self.rules())
        self.metadata(
            "consumer",
            lambda value: value["module"].update(
                includes=[{"kind": "module", "target": "module.app", "reason": " "}]
            ),
        )
        self.assertIn("CHK.includes.reason", self.rules())
        self.metadata(
            "consumer",
            lambda value: value["module"].update(
                includes=[],
                uses=[{"target": "module.unknown", "meaning": "#uses-module-provider"}],
            ),
        )
        with self.assertRaisesRegex(SpecError, "CHK.relation.endpoints"):
            self.project.repository()
        self.assertIn("CHK.relation.endpoints", self.rules())

    @verifies("scenario.spec.meaning-relations")
    def test_relations_between_meanings(self):
        self.relation(
            "provider",
            {
                "type": "narrows",
                "source": "concept.provider.thing",
                "target": "concept.provider.thing",
            },
        )
        self.assertIn("CHK.narrows.acyclic", self.rules())
        self.metadata(
            "provider", lambda value: value.update(relations=value["relations"][:1])
        )
        self.relation(
            "provider",
            {
                "type": "supersedes",
                "source": "concept.provider.thing",
                "target": "concept.provider.thing",
            },
        )
        self.assertIn("CHK.concept.retired", self.rules())
        self.metadata(
            "provider", lambda value: value.update(relations=value["relations"][:1])
        )
        for _ in range(2):
            self.relation(
                "consumer",
                {
                    "type": "contrasts",
                    "source": "concept.provider.thing",
                    "target": "module.consumer",
                    "reason": "different",
                },
            )
        rules = self.rules()
        self.assertIn("CHK.contrasts.once", rules)
        self.assertIn("CHK.relation.site", rules)
        self.metadata(
            "consumer", lambda value: value.update(relations=value["relations"][:1])
        )
        self.relation(
            "consumer",
            {
                "type": "relates",
                "source": "realization.consumer.view",
                "verb": " ",
                "target": "module.provider",
            },
        )
        self.assertIn("CHK.relates.verb", self.rules())
        self.metadata(
            "consumer", lambda value: value.update(relations=value["relations"][:1])
        )
        self.relation(
            "consumer",
            {
                "type": "relates",
                "source": "realization.provider.store",
                "verb": "feeds",
                "target": "module.consumer",
            },
        )
        self.assertIn("CHK.relates.source", self.rules())
        self.metadata(
            "consumer", lambda value: value.update(relations=value["relations"][:1])
        )
        self.relation(
            "consumer",
            {
                "type": "relates",
                "source": "module.consumer",
                "verb": "reads things from",
                "target": "module.provider",
            },
        )
        self.assertEqual(
            set(),
            self.rules()
            & {"CHK.relates.source", "CHK.relation.site", "CHK.relates.verb"},
        )
        self.relation(
            "consumer",
            {"type": "uses", "source": "module.consumer", "target": "module.provider"},
        )
        self.assertIn("CHK.relation.site", self.rules())
        self.metadata(
            "consumer", lambda value: value.update(relations=value["relations"][:2])
        )
        self.relation(
            "consumer",
            {
                "type": "depends",
                "source": "module.consumer",
                "target": "module.provider",
            },
        )
        self.assertIn("CHK.relation.type", self.rules())

    @verifies("scenario.spec.name-collision")
    def test_same_named_nodes_of_different_owners_need_a_contrast(self):
        def concept(title):
            self.metadata(
                "consumer",
                lambda value: value["defines"].append(
                    {
                        "id": "concept.consumer.thing",
                        "type": "concept",
                        "title": title,
                        "meaning": "#concept.consumer.thing",
                    }
                ),
            )
            self.edit(
                self.entry("consumer"),
                "| [Thing](../provider/module.md#concept.provider.thing) | |",
                f"| {title} | A shown value. |\n| [Thing](../provider/module.md#concept.provider.thing) | |",
            )
            self.edit(
                self.entry("consumer"),
                "## Relationships",
                '<a id="concept.consumer.thing"></a>\n\nWhat a person sees.\n\n## Relationships',
            )

        concept("THING")
        self.assertIn("CHK.contrasts.required", self.rules())
        self.relation(
            "consumer",
            {
                "type": "contrasts",
                "source": "concept.consumer.thing",
                "target": "concept.provider.thing",
                "reason": "a shown copy, not the stored value",
            },
        )
        self.assertNotIn("CHK.contrasts.required", self.rules())
        self.edit(
            self.entry("consumer"),
            "| THING | A shown value. |",
            "| PROVIDER | A shown value. |",
        )
        self.metadata(
            "consumer", lambda value: value["defines"][-1].update(title="PROVIDER")
        )
        self.assertIn("CHK.contrasts.required", self.rules())
        self.edit(
            self.entry("consumer"),
            "| PROVIDER | A shown value. |",
            "| consumer | A shown value. |",
        )
        self.metadata(
            "consumer", lambda value: value["defines"][-1].update(title="consumer")
        )
        self.assertNotIn(
            "concept.consumer.thing",
            [f.subject_id for f in self.project.findings("CHK.contrasts.required")],
        )

    @verifies("scenario.spec.participation")
    def test_contract_participation(self):
        contract = {
            "id": "contract.provider.read",
            "version": 2,
            "schema": {"type": "integer"},
            "semantics": "The stored count.",
            "example": 3,
        }
        with (self.root / "specs/provider/obligations.md").open("a") as stream:
            stream.write("\n## Contracts\n\n" + block("concorde-contract", contract))

        def participate(module, role, peer, version):
            self.metadata(
                module,
                lambda value: value["module"]["participates"].append(
                    {
                        "contract": "contract.provider.read",
                        "version": version,
                        "role": role,
                        "peer": peer,
                        "meaning": "#uses-module-provider"
                        if module == "consumer"
                        else "#concept.provider.thing",
                    }
                ),
            )

        participate("provider", "provided", "module.consumer", 2)
        self.assertIn("CHK.participates.complementary", self.rules())
        participate("consumer", "required", "module.provider", 1)
        rules = self.rules()
        self.assertIn("CHK.participates.version", rules)
        self.metadata(
            "consumer",
            lambda value: value["module"]["participates"][0].update(version=2),
        )
        self.assertEqual(
            set(),
            self.rules()
            & {"CHK.participates.version", "CHK.participates.complementary"},
        )
        participate("consumer", "required", "module.provider", 2)
        self.assertIn("CHK.participates.unique", self.rules())

    @verifies("scenario.spec.validate-architecture-mismatch")
    def test_checked_flowcharts_assert_only_declared_relations(self):
        entry = self.entry("consumer")
        original = (self.root / entry).read_text()
        cases = {
            "CHK.view.nodes": original.replace(
                'thing["Provider / Thing"]', 'thing["Widget"]'
            ),
            "CHK.view.edges": original.replace("-->|shows|", "-->"),
            "CHK.view.edges ": original.replace(
                'view["View"] -->|shows| thing["Provider / Thing"]',
                'thing["Provider / Thing"] -->|shows| view["View"]',
            ),
            "CHK.view.marked": original
            + "\n```mermaid\nsequenceDiagram\n    A->>B: hi\n```\n",
            # A reversed arrow points from its right node to its left one.
            "CHK.view.edges  ": original.replace(
                'view["View"] -->|shows| thing["Provider / Thing"]',
                'view["View"] <--|shows| thing["Provider / Thing"]',
            ),
            # An edge without one direction asserts no declared relation.
            "CHK.view.edges   ": original.replace("-->|shows|", "---|shows|"),
            "CHK.view.edges    ": original.replace("-->|shows|", "<-->|shows|"),
        }
        for rule, text in cases.items():
            with self.subTest(rule):
                (self.root / entry).write_text(text)
                self.assertIn(rule.strip(), self.rules())
        # The declared direction drawn with a reversed arrow is accepted.
        (self.root / entry).write_text(
            original.replace(
                'view["View"] -->|shows| thing["Provider / Thing"]',
                'thing["Provider / Thing"] <--|shows| view["View"]',
            )
        )
        self.assertNotIn("CHK.view.edges", self.rules())
        (self.root / entry).write_text(
            original
            + "\n```mermaid illustrative\nsequenceDiagram\n    A->>B: hi\n```\n"
            + "\n```mermaid illustrative\nflowchart LR\n    x[Anything] --> y[Else]\n```\n"
        )
        self.assertEqual(
            set(),
            self.rules() & {"CHK.view.marked", "CHK.view.nodes", "CHK.view.edges"},
        )
        # A label matching both a local node and a Module title is ambiguous.
        self.edit(
            self.entry("provider"),
            "| Thing | One stored value with an identity. |",
            "| Consumer | Someone who reads. |\n| Thing | One stored value with an identity. |",
        )
        self.metadata(
            "provider",
            lambda value: value["defines"].append(
                {
                    "id": "concept.provider.consumer",
                    "type": "concept",
                    "title": "Consumer",
                    "meaning": "#concept.provider.thing",
                }
            ),
        )
        self.edit(
            self.entry("provider"),
            'flowchart LR\n    store["Store"] -->|holds| thing["Thing"]',
            'flowchart LR\n    store["Store"] -->|holds| thing["Thing"]\n    c["Consumer"]',
        )
        self.assertIn("CHK.view.nodes", self.rules())

    @verifies("scenario.spec.registry-mirror", "scenario.spec.registry-regenerate")
    def test_a_stale_registry_is_reported_and_regenerated(self):
        value = self.project.metadata(self.entry("consumer"))
        value["module"]["includes"].append(
            {"kind": "module", "target": "module.app", "reason": "the app's purpose"}
        )
        self.project.save_metadata(self.entry("consumer"), value)
        findings = self.project.findings("CHK.registry.mirror")
        self.assertEqual(["module.consumer"], [f.subject_id for f in findings])
        before = (self.root / ".concorde/specs.json").read_bytes()
        checked = registry_command(self.root, write=False)
        self.assertEqual("invalid", checked.status)
        self.assertEqual(["module.consumer"], [f.subject_id for f in checked.findings])
        self.assertEqual(before, (self.root / ".concorde/specs.json").read_bytes())
        written = registry_command(self.root, write=True)
        self.assertEqual("success", written.status)
        registry = read_json(self.root, ".concorde/specs.json")
        self.assertEqual(
            ["module.app", "module.provider", "module.consumer"],
            [m["id"] for m in registry["modules"]],
        )
        self.assertEqual(
            value["module"]["includes"], registry["modules"][2]["includes"]
        )
        self.assertEqual([], self.project.findings("CHK.registry.mirror"))
        self.assertEqual("unchanged", registry_command(self.root, write=True).status)
        # The title is a mirrored field too: a renamed record is stale and regenerated.
        title = registry["modules"][2]["title"]
        registry["modules"][2]["title"] = "Renamed"
        write_json(self.root, ".concorde/specs.json", registry)
        self.assertIn("CHK.registry.mirror", self.rules())
        self.assertEqual(
            ["module.consumer"],
            [f.subject_id for f in registry_command(self.root, write=False).findings],
        )
        registry_command(self.root, write=True)
        self.assertEqual(
            title,
            read_json(self.root, ".concorde/specs.json")["modules"][2]["title"],
        )
        self.assertEqual([], self.project.findings("CHK.registry.mirror"))

    @verifies("scenario.spec.reject-inconsistent-inventory")
    def test_an_unreadable_registry_yields_no_repository(self):
        path = self.root / ".concorde/specs.json"
        original = path.read_text()
        for text in (
            "{not json",
            '{"schema_version": 3, "schema_version": 3, "modules": []}',
            original.replace('"schema_version": 3', '"schema_version": 5'),
        ):
            with self.subTest(text=text[:30]):
                path.write_text(text)
                with self.assertRaises(SpecError):
                    self.project.repository()
                report = self.project.validate()
                self.assertEqual("invalid", report.status)
                self.assertIn(
                    "CONCORDE-SOURCE-008", {f.rule_id for f in report.findings}
                )

    @verifies("scenario.spec.validate-structural-errors", "scenario.spec.unbound-file")
    def test_every_violation_is_reported_in_one_run(self):
        subprocess.run(("git", "init", "-q"), cwd=self.root, check=True)
        self.project.write("scripts/export.py", "print('export')\n")
        self.project.write("generated/out.txt", "rendered\n")
        subprocess.run(("git", "add", "-A"), cwd=self.root, check=True)
        self.metadata(
            "consumer",
            lambda value: value["module"]["uses"].append(
                {"target": "module.consumer", "meaning": "#uses-module-provider"}
            ),
        )
        self.edit(
            "specs/consumer/obligations.md",
            "scenario.consumer.show",
            "scenario.provider.read",
        )
        report = self.project.validate()
        self.assertEqual("invalid", report.status)
        rules = {f.rule_id for f in report.findings}
        self.assertTrue(
            {"CHK.uses.no-self", "CHK.defines.once", "CHK.binds.unbound"} <= rules,
            rules,
        )
        unbound = [
            f.source for f in report.findings if f.rule_id == "CHK.binds.unbound"
        ]
        self.assertEqual(["scripts/export.py"], unbound)
        for finding in report.findings:
            self.assertTrue(finding.remediation)

    @verifies("scenario.spec.unbound-file")
    def test_bound_document_members_and_generated_outputs_are_never_bound(self):
        self.metadata(
            "consumer",
            lambda value: value["defines"][0].update(
                entries=["src/consumer.py", "specs/provider/module.md.json"]
            ),
        )
        self.assertIn("CHK.binds.no-spec", self.rules())

    def test_link_fragments_name_definitions_in_the_linked_document(self):
        self.edit(
            self.entry("consumer"),
            "Renders one thing.",
            "Renders one [thing](../provider/obligations.md#concept.provider.thing) and "
            "[an unknown one](#req.consumer.missing) under [Purpose](#purpose).",
        )
        findings = self.project.findings("CONCORDE-LINK-001")
        self.assertEqual(2, len(findings), [f.message for f in findings])


if __name__ == "__main__":
    unittest.main()
