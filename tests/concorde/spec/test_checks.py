"""Every family of Protocol 13 structural checks, each on a small fixture project."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.spec.registry import registry_command
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import (
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
    'store: Store {\n  "provider.py"\n}\nthing: Thing\nstore -> thing: holds',
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
    "view: View\nthing: Provider / Thing\nconsumer: Consumer\nprovider: Provider\n"
    "view -> thing: shows\nconsumer -> provider",
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
    "app: App {\n  provider: Provider\n  consumer: Consumer\n}",
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
        # The sections may come in any order, and further sections may be added.
        reordered = (
            original.replace("## Usage", "## Tmp")
            .replace("## Design", "## Usage")
            .replace("## Tmp", "## Design")
        )
        (self.root / entry).write_text(reordered + "\n## Structure\n\nMore detail.\n")
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
            "consumer -> provider\n",
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

    @verifies("scenario.spec.composition-checks", "scenario.spec.multiple-roots")
    def test_more_than_one_root_is_a_warning(self):
        self.metadata(
            "app",
            lambda value: value["module"].update(
                contains=value["module"]["contains"][:1]
            ),
        )
        self.edit(self.entry("app"), "  consumer: Consumer\n", "")
        self.assertIn("CHK.contains.root", self.rules("warning"))
        self.assertNotIn("CHK.contains.root", self.rules())

    @verifies("scenario.spec.relies-on", "scenario.spec.relies-on-invalid")
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

    @verifies("scenario.spec.name-collision", "scenario.spec.name-collision-contrasted")
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
    def test_checked_diagrams_assert_only_declared_relations(self):
        entry = self.entry("consumer")
        original = (self.root / entry).read_text()
        provider = self.entry("provider")
        provider_original = (self.root / provider).read_text()
        cases = {
            "CHK.view.nodes": original.replace(
                "thing: Provider / Thing", "thing: Widget"
            ),
            # An edge that touches a node carries the verb of its relates.
            "CHK.view.edges": original.replace("view -> thing: shows", "view -> thing"),
            "CHK.view.edges ": original.replace(
                "view -> thing: shows", "thing -> view: shows"
            ),
            # An unlabelled edge between Modules is a uses in the drawn direction.
            "CHK.view.edges  ": original.replace(
                "consumer -> provider", "provider -> consumer"
            ),
            # A labelled edge between Modules is a relates, and none is declared here.
            "CHK.view.edges   ": original.replace(
                "consumer -> provider", "consumer -> provider: reads things from"
            ),
            # A qualified node drawn inside a Module that does not own it.
            "CHK.view.nesting": original.replace(
                "consumer: Consumer\n",
                "consumer: Consumer {\n  store: Provider / Store\n}\n",
            ),
            # A Module drawn inside one that does not contain it.
            "CHK.view.nesting ": original.replace(
                "provider: Provider\n", "provider: Provider {\n  inner: Consumer\n}\n"
            ),
            "CHK.view.subset": original.replace(
                "view -> thing: shows", "view <- thing: shows"
            ),
            "CHK.view.subset ": original.replace(
                "consumer -> provider", "consumer -> provider\nview.style.fill: red"
            ),
            "CHK.view.marked": original
            + "\n```mermaid\nsequenceDiagram\n    A->>B: hi\n```\n",
        }
        for rule, text in cases.items():
            with self.subTest(rule):
                (self.root / entry).write_text(text)
                self.assertIn(rule.strip(), self.rules())
        (self.root / entry).write_text(original)
        for rule, text in {
            # A file shape names an entry its realization binds.
            "CHK.view.nodes": provider_original.replace(
                '"provider.py"', '"missing.py"'
            ),
            # A file shape asserts only its binding and has no edges.
            "CHK.view.edges": provider_original.replace(
                "store -> thing: holds",
                'store -> thing: holds\nstore."provider.py" -> thing: holds',
            ),
            # Only a Module holds nodes.
            "CHK.view.nesting": provider_original.replace(
                "thing: Thing", "thing: Thing {\n  inner: Store\n}"
            ),
        }.items():
            with self.subTest(rule):
                (self.root / provider).write_text(text)
                self.assertIn(rule, self.rules())
        (self.root / provider).write_text(provider_original)
        # A checked diagram belongs to module reading only.
        obligations = self.root / "specs/consumer/obligations.md"
        obligations_original = obligations.read_text()
        obligations.write_text(
            obligations_original + "\n```d2\nconsumer: Consumer\n```\n"
        )
        self.assertIn("CHK.view.marked", self.rules())
        obligations.write_text(
            obligations_original + "\n```d2 illustrative\nconsumer: Consumer\n```\n"
        )
        self.assertNotIn("CHK.view.marked", self.rules())
        obligations.write_text(obligations_original)
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
            "store -> thing: holds",
            "store -> thing: holds\nc: Consumer",
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

    @verifies("scenario.spec.unbound-file", "scenario.spec.bound-spec-member")
    def test_bound_document_members_and_generated_outputs_are_never_bound(self):
        for entries in (
            ["src/consumer.py", "specs/provider/module.md.json"],
            ["src/consumer.py", "specs/provider/"],
        ):
            with self.subTest(entries=entries):
                self.metadata(
                    "consumer",
                    lambda value, entries=entries: value["defines"][0].update(
                        entries=entries
                    ),
                )
                findings = self.project.findings("CHK.binds.no-spec")
                self.assertEqual(1, len(findings), [f.message for f in findings])
                self.assertIn(f"binds {entries[1]},", findings[0].message)
                self.assertEqual("realization.consumer.view", findings[0].subject_id)

    def snapshot(self):
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    @verifies("scenario.spec.validate-unreadable-registry")
    def test_an_unreadable_registry_is_one_finding_and_no_exception(self):
        (self.root / ".concorde/specs.json").write_text("{not json")
        before = self.snapshot()
        report = self.project.validate()
        self.assertEqual("invalid", report.status)
        errors = [f for f in report.findings if f.severity == "error"]
        self.assertEqual(["CONCORDE-SOURCE-008"], [f.rule_id for f in errors])
        self.assertIn("JSON", errors[0].message)
        load = report.result["load_error"]
        self.assertEqual(
            (".concorde/specs.json", "unsupported_profile"),
            (load["location"]["path"], load["code"]),
        )
        self.assertIn("strict JSON", load["reason"])
        self.assertIn("strict JSON", errors[0].remediation)
        self.assertEqual(before, self.snapshot())

    @verifies("scenario.spec.node-unexplained")
    def test_an_anchor_followed_only_by_links_is_a_warning(self):
        self.edit(
            self.entry("consumer"),
            "Renders one thing.",
            "[Provider](../provider/module.md)\n\n### Rendering",
        )
        findings = self.project.findings("CHK.node.explained")
        self.assertEqual(["warning"], [f.severity for f in findings])
        self.assertEqual("specs/consumer/module.md", findings[0].source)
        self.assertEqual("success", self.project.validate().status)

    @verifies("scenario.spec.terminology-import-invalid")
    def test_malformed_terminology_rows_are_errors(self):
        entry = self.entry("consumer")
        original = (self.root / entry).read_text()
        cases = {
            # An import row that carries a definition.
            "CHK.terminology.import-row": original.replace(
                "| [Thing](../provider/module.md#concept.provider.thing) | |",
                "| [Thing](../provider/module.md#concept.provider.thing) | A copied definition. |",
            ),
            # A defining row with no matching concept.
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
        # A topic of the provider imports the provider's own concept.
        topic = DocumentSource(
            "# Rules\n\nHow things are kept.\n\n## Terminology\n\n"
            "| Term | Definition |\n| --- | --- |\n"
            "| [Thing](module.md#concept.provider.thing) | |\n\n"
            "## Keeping\n\nThings are kept until removed.\n",
            {
                "schema_version": 3,
                "document": {
                    "id": "document.provider.rules",
                    "owner": "module.provider",
                    "role": "module",
                },
                "defines": [],
                "relations": [],
            },
        )
        self.project.write("specs/provider/rules.md", topic)
        self.metadata(
            "provider",
            lambda value: value["module"]["owns"].append("specs/provider/rules.md"),
        )
        findings = self.project.findings("CHK.imports.foreign")
        self.assertEqual(
            [("error", "specs/provider/rules.md", "concept.provider.thing")],
            [(f.severity, f.source, f.subject_id) for f in findings],
        )

    @verifies("scenario.spec.import-owner-warning")
    def test_an_import_from_an_unrelated_module_in_context_is_a_warning(self):
        self.metadata(
            "consumer",
            lambda value: value["module"].update(
                uses=[],
                includes=[
                    {
                        "kind": "document",
                        "target": "document.provider.module",
                        "reason": "the Thing definition",
                    }
                ],
            ),
        )
        self.edit(
            self.entry("consumer"),
            "consumer -> provider\n",
            "",
        )
        self.assertNotIn("CHK.context.reconciled", self.rules())
        findings = self.project.findings("CHK.imports.owner")
        self.assertEqual(
            [("warning", "specs/consumer/module.md", "concept.provider.thing")],
            [(f.severity, f.source, f.subject_id) for f in findings],
        )
        self.assertIn("module.provider", findings[0].message)

    @verifies("scenario.spec.mutual-uses")
    def test_two_modules_that_use_each_other_select_each_other_one_level(self):
        self.metadata(
            "provider",
            lambda value: value["module"]["uses"].append(
                {"target": "module.consumer", "meaning": "#notifies"}
            ),
        )
        self.edit(
            self.entry("provider"),
            "The store holds every thing.",
            'The store holds every thing.\n\n<a id="notifies"></a>\n\n'
            "The provider notifies the consumer of new things.",
        )
        report = self.project.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertEqual(
            set(),
            {
                f.rule_id
                for f in report.findings
                if f.rule_id.startswith(("CHK.uses.", "CHK.contains."))
            },
        )
        repository = self.project.repository()
        provider = repository.spec_context("module.provider").paths
        consumer = repository.spec_context("module.consumer").paths
        for path in ("specs/consumer/module.md", "specs/consumer/obligations.md"):
            self.assertIn(path, provider)
        for path in ("specs/provider/module.md", "specs/provider/obligations.md"):
            self.assertIn(path, consumer)
        # One level deep: neither context follows the other's relations to the parent.
        self.assertNotIn("specs/app/module.md", provider)
        self.assertNotIn("specs/app/module.md", consumer)

    @verifies("scenario.spec.includes-redundant")
    def test_a_redundant_inclusion_is_a_warning_and_selects_once(self):
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
        findings = self.project.findings("CHK.includes.redundant")
        self.assertEqual(
            [("warning", "module.consumer")],
            [(f.severity, f.subject_id) for f in findings],
        )
        self.assertEqual("success", self.project.validate().status)
        sources = (
            self.project.repository().spec_context("module.consumer").value["sources"]
        )
        entries = [s for s in sources if s["path"] == "specs/provider/module.md"]
        self.assertEqual(1, len(entries))
        self.assertEqual(
            [
                {
                    "relation": "includes",
                    "kind": "document",
                    "id": "document.provider.module",
                },
                {"relation": "uses", "id": "module.provider"},
            ],
            entries[0]["reasons"],
        )

    @verifies("scenario.spec.relates-module-source")
    def test_a_module_may_be_the_source_of_relates(self):
        self.relation(
            "consumer",
            {
                "type": "relates",
                "source": "module.consumer",
                "verb": "reads things from",
                "target": "module.provider",
            },
        )
        report = self.project.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertEqual({"CONCORDE-COVERAGE-001"}, self.rules("warning"))

    @verifies("scenario.spec.checked-diagram")
    def test_a_checked_diagram_that_asserts_only_declarations_passes(self):
        entry = self.entry("consumer")
        # Local realization, qualified provider concept and Module titles, each edge declared.
        text = (self.root / entry).read_text()
        self.assertIn("view -> thing: shows", text)
        self.assertIn("consumer -> provider\n", text)
        # The provider draws its realization with the file it binds.
        self.assertIn(
            'store: Store {\n  "provider.py"\n}',
            (self.root / self.entry("provider")).read_text(),
        )
        # The root nests its children, which asserts its contains.
        self.assertIn(
            "app: App {\n  provider: Provider",
            (self.root / "specs/app/module.md").read_text(),
        )
        (self.root / entry).write_text(
            text
            + "\n```d2\n# quoted keys, dotted paths and comments\n"
            + '"the app": App {\n  consumer: Consumer\n}\n'
            + '"the app".consumer -> provider; provider: Provider\n```\n'
            + "\n```d2 illustrative\nx: Anything {style.fill: red}\nx -> y: feeds\n```\n"
            + "\n```d2 illustrative\nshape: sequence_diagram\na -> b: hi\n```\n"
        )
        report = self.project.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertEqual(
            [],
            [f.rule_id for f in report.findings if f.rule_id.startswith("CHK.view.")],
        )

    @verifies("scenario.spec.check-input-missing")
    def test_a_configured_check_with_a_missing_or_linked_input_is_an_error(self):
        (self.root / "data").mkdir()
        (self.root / "data/real.txt").write_text("input\n")
        (self.root / "data/link.txt").symlink_to("real.txt")
        config = read_json(self.root, ".concorde/config.json")
        config["checks"] = [
            {
                "id": "check.consumer",
                "module": "module.consumer",
                "argv": ["{python}", "-c", "open('ran', 'w').close()"],
                "timeout_seconds": 10,
                "inputs": ["data/missing.txt", "data/link.txt", "data/real.txt"],
            }
        ]
        write_json(self.root, ".concorde/config.json", config)
        findings = self.project.findings("CONCORDE-CHECK-001")
        self.assertEqual(
            [
                ("error", "data/link.txt", "check.consumer"),
                ("error", "data/missing.txt", "check.consumer"),
            ],
            sorted((f.severity, f.source, f.subject_id) for f in findings),
        )
        for finding in findings:
            self.assertIn("check.consumer", finding.message)
            self.assertIn(finding.source, finding.message)
        self.assertFalse((self.root / "ran").exists())

    @verifies("scenario.spec.registry-check")
    def test_checking_the_registry_reports_each_stale_record_and_writes_nothing(self):
        self.project.save_metadata(
            self.entry("consumer"),
            {
                **self.project.metadata(self.entry("consumer")),
                "module": {
                    **self.project.metadata(self.entry("consumer"))["module"],
                    "title": "Viewer",
                },
            },
        )
        registry = read_json(self.root, ".concorde/specs.json")
        registry["modules"][1]["owns"] = registry["modules"][1]["owns"][:1]
        write_json(self.root, ".concorde/specs.json", registry)
        before = self.snapshot()
        checked = registry_command(self.root, write=False)
        self.assertEqual("invalid", checked.status)
        self.assertEqual(
            [
                ("CHK.registry.mirror", "module.consumer"),
                ("CHK.registry.mirror", "module.provider"),
            ],
            sorted((f.rule_id, f.subject_id) for f in checked.findings),
        )
        self.assertEqual(before, self.snapshot())

    @verifies("scenario.spec.unbound-exemptions")
    def test_documents_control_records_generated_outputs_and_external_material_need_no_binding(
        self,
    ):
        subprocess.run(("git", "init", "-q"), cwd=self.root, check=True)
        self.project.write("generated/out.txt", "rendered\n")
        self.project.write(".concorde/reflections/note.json", "{}\n")
        self.project.write("references/lib/api.md", "## connect(url)\n")
        self.project.write("scripts/export.py", "print('export')\n")
        self.metadata(
            "consumer",
            lambda value: value["module"]["includes"].append(
                {
                    "kind": "external",
                    "target": "references/lib/",
                    "reason": "the library API",
                }
            ),
        )
        subprocess.run(("git", "add", "-A"), cwd=self.root, check=True)
        tracked = subprocess.run(
            ("git", "ls-files"),
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        for path in (
            "specs/provider/module.md",
            "specs/provider/module.md.json",
            ".concorde/specs.json",
            "generated/out.txt",
            "references/lib/api.md",
        ):
            self.assertIn(path, tracked)
        # Only the source file no realization covers is reported.
        self.assertEqual(
            ["scripts/export.py"],
            [f.source for f in self.project.findings("CHK.binds.unbound")],
        )

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
