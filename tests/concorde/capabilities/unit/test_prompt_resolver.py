from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.prompt_resolver import (  # noqa: E402
    PromptResolverError,
    check_reachability,
    find_unreachable_prompts,
    resolve_role_prompt,
    resolve_skill_source,
)


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _prompt(audience: str, body: str) -> str:
    return f"---\naudience: {audience}\n---\n\n{body}"


class PromptResolverRuleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    # --- 1. cycle -----------------------------------------------------

    def test_cycle_between_two_prompts_is_rejected(self):
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "A body\n\n@include prompts/workflow-host/b.md\n"))
        _write(self.root, "prompts/workflow-host/b.md", _prompt("worker", "B body\n\n@include prompts/workflow-host/a.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-CYCLE-001")

    def test_self_cycle_is_rejected(self):
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include prompts/workflow-host/a.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-CYCLE-001")

    # --- 2. diamond: same file reached twice within one root ----------

    def test_diamond_inclusion_is_rejected_and_reports_both_paths(self):
        _write(
            self.root,
            "prompts/workflow-host/root.md",
            _prompt("worker", "Root\n\n@include prompts/workflow-host/left.md\n\n@include prompts/workflow-host/right.md\n"),
        )
        _write(self.root, "prompts/workflow-host/left.md", _prompt("worker", "Left\n\n@include prompts/workflow-host/shared.md\n"))
        _write(self.root, "prompts/workflow-host/right.md", _prompt("worker", "Right\n\n@include prompts/workflow-host/shared.md\n"))
        _write(self.root, "prompts/workflow-host/shared.md", _prompt("worker", "Shared text\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/root.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-DIAMOND-001")
        message = str(context.exception)
        self.assertIn("left.md", message)
        self.assertIn("right.md", message)

    def test_same_root_can_be_resolved_twice_without_diamond(self):
        _write(self.root, "prompts/workflow-host/shared.md", _prompt("worker", "Shared\n"))
        _write(self.root, "prompts/workflow-host/one.md", _prompt("worker", "One\n\n@include prompts/workflow-host/shared.md\n"))
        _write(self.root, "prompts/workflow-host/two.md", _prompt("worker", "Two\n\n@include prompts/workflow-host/shared.md\n"))
        one = resolve_role_prompt(self.root, "prompts/workflow-host/one.md")
        two = resolve_role_prompt(self.root, "prompts/workflow-host/two.md")
        self.assertIn("Shared", one.body)
        self.assertIn("Shared", two.body)

    # --- 3. missing target ---------------------------------------------

    def test_missing_include_target_is_rejected(self):
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include prompts/workflow-host/missing.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-MISSING-001")

    def test_unsafe_include_path_is_rejected(self):
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include ../outside.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-MISSING-001")

    # --- 4. unresolved directive or variable ----------------------------

    def test_unbound_variable_is_rejected(self):
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("worker", "Hello {NAME}.\n"))
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include prompts/workflow-host/leaf.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-UNRESOLVED-001")

    def test_malformed_directive_is_rejected(self):
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-UNRESOLVED-001")

    def test_directive_with_bad_parameter_syntax_is_rejected(self):
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("worker", "Leaf\n"))
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include prompts/workflow-host/leaf.md not-a-key-value\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-UNRESOLVED-001")

    def test_reserved_variables_pass_through_unresolved(self):
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("ambient", "Run `{OPERATION}` with {SCRIPT} under {FRAMEWORK}.\n"))
        _write(self.root, "skills/concorde-x/SKILL.md", '---\nname: concorde-x\ndescription: "X"\ncapability: x\n---\n\n@include prompts/workflow-host/leaf.md\n')
        result = resolve_skill_source(self.root, "skills/concorde-x/SKILL.md")
        self.assertIn("{OPERATION}", result.body)
        self.assertIn("{SCRIPT}", result.body)
        self.assertIn("{FRAMEWORK}", result.body)

    def test_prompt_with_invalid_audience_is_rejected(self):
        _write(self.root, "prompts/workflow-host/a.md", _prompt("nonsense", "Body\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-AUDIENCE-002")

    # --- 5. audience incompatibility -------------------------------------

    def test_worker_root_cannot_include_ambient_prompt(self):
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("ambient", "Ambient text\n"))
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include prompts/workflow-host/leaf.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-AUDIENCE-001")

    def test_ambient_root_cannot_include_worker_prompt(self):
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("worker", "Worker text\n"))
        _write(
            self.root,
            "skills/concorde-x/SKILL.md",
            '---\nname: concorde-x\ndescription: "X"\ncapability: x\n---\n\n@include prompts/workflow-host/leaf.md\n',
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_skill_source(self.root, "skills/concorde-x/SKILL.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-AUDIENCE-001")

    def test_shared_prompt_is_includable_from_either_audience(self):
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("shared", "Shared text\n"))
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include prompts/workflow-host/leaf.md\n"))
        _write(
            self.root,
            "skills/concorde-x/SKILL.md",
            '---\nname: concorde-x\ndescription: "X"\ncapability: x\n---\n\n@include prompts/workflow-host/leaf.md\n',
        )
        role_result = resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        skill_result = resolve_skill_source(self.root, "skills/concorde-x/SKILL.md")
        self.assertIn("Shared text", role_result.body)
        self.assertIn("Shared text", skill_result.body)

    # --- 6. include of a skill source or of anything under specs/ -------

    def test_include_of_skill_source_is_rejected(self):
        _write(self.root, "skills/concorde-x/SKILL.md", '---\nname: concorde-x\ndescription: "X"\ncapability: x\n---\n\nBody\n')
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include skills/concorde-x/SKILL.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-SCOPE-001")

    def test_include_of_spec_document_is_rejected(self):
        _write(self.root, "specs/example/system.md", "# Example\n")
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include specs/example/system.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-SCOPE-001")

    # --- 7. crossing the prompts/protocol/ boundary ----------------------

    def test_protocol_prompt_cannot_include_outside_protocol(self):
        _write(self.root, "prompts/protocol/principles.md", _prompt("shared", "@include prompts/workflow-host/leaf.md\n"))
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("shared", "Leaf\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/protocol/principles.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-PROTOCOL-001")

    def test_non_protocol_prompt_cannot_include_protocol(self):
        _write(self.root, "prompts/protocol/principles.md", _prompt("shared", "Principles\n"))
        _write(self.root, "prompts/workflow-host/a.md", _prompt("worker", "@include prompts/protocol/principles.md\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-PROTOCOL-001")

    def test_protocol_prompt_may_include_another_protocol_prompt(self):
        _write(self.root, "prompts/protocol/principles.md", _prompt("shared", "@include prompts/protocol/kinds.md\n"))
        _write(self.root, "prompts/protocol/kinds.md", _prompt("shared", "Kinds\n"))
        result = resolve_role_prompt(self.root, "prompts/protocol/principles.md")
        self.assertIn("Kinds", result.body)

    # --- 8. unreachable prompt files given a set of roots ----------------

    def test_unreachable_prompt_is_reported(self):
        _write(self.root, "prompts/workflow-host/root.md", _prompt("worker", "Root only\n"))
        _write(self.root, "prompts/workflow-host/orphan.md", _prompt("worker", "Never included\n"))
        unreachable = find_unreachable_prompts(self.root, ["prompts/workflow-host/root.md"])
        self.assertEqual(unreachable, ("prompts/workflow-host/orphan.md",))
        with self.assertRaises(PromptResolverError) as context:
            check_reachability(self.root, ["prompts/workflow-host/root.md"])
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-UNREACHABLE-001")

    def test_every_prompt_reachable_reports_no_gap(self):
        _write(self.root, "prompts/workflow-host/root.md", _prompt("worker", "@include prompts/workflow-host/leaf.md\n"))
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("worker", "Leaf\n"))
        unreachable = find_unreachable_prompts(self.root, ["prompts/workflow-host/root.md"])
        self.assertEqual(unreachable, ())
        check_reachability(self.root, ["prompts/workflow-host/root.md"])  # must not raise


if __name__ == "__main__":
    unittest.main()
