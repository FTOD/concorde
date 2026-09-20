from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.prompt_resolver import (  # noqa: E402
    PromptResolverError,
    check_reachability,
    find_unreachable_prompts,
    resolve_model_instructions,
    resolve_operation_guidance,
    resolve_role_prompt,
)


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _prompt(audience: str, body: str) -> str:
    return f"---\naudience: {audience}\n---\n\n{body}"


from concorde.spec.verification import verifies  # noqa: E402


class PromptResolverRuleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    @verifies("scenario.distribution.prompt-references")
    def test_nested_references_bind_quoted_values_and_track_sources(self):
        _write(
            self.root, "prompts/leaf.md", _prompt("shared", "Hello {NAME}: {ACTION}.\n")
        )
        _write(
            self.root,
            "prompts/middle.md",
            _prompt(
                "worker", "@prompts/leaf.md NAME=\"{NAME}\" ACTION='check carefully'\n"
            ),
        )
        _write(
            self.root,
            "operations/example/spec.md",
            '# Example\n@prompts/middle.md NAME="Ada Lovelace"\nDone.\n',
        )
        result = resolve_model_instructions(self.root, "operations/example/spec.md")
        self.assertEqual(
            "# Example\nHello Ada Lovelace: check carefully.\nDone.\n", result.body
        )
        self.assertEqual(
            ("operations/example/spec.md", "prompts/leaf.md", "prompts/middle.md"),
            result.sources,
        )

    @verifies("scenario.distribution.prompt-references")
    def test_literal_markdown_is_not_a_reference(self):
        body = (
            "Contact person@example.md or @person.\n"
            "@person\n@person@example.md\n@decorator(value)\n@functools.cache\n"
            "@\n@ path.md\nInline @prompts/missing.md\n"
            " @prompts/missing.md\n\t@prompts/missing.md\n"
            "`@prompts/missing.md`\n@include-example\n"
            "Use `@include path.md` as a historical example.\n"
            " @include path.md\n"
        )
        _write(self.root, "prompts/root.md", _prompt("worker", body))
        self.assertEqual(body, resolve_role_prompt(self.root, "prompts/root.md").body)

    @verifies("scenario.distribution.prompt-references")
    def test_retired_syntax_is_rejected_for_all_roots_and_nested_sources(self):
        for directive in (
            "@include",
            "@include prompts/leaf.md",
            "@include\tprompts/leaf.md",
        ):
            for nested in (False, True):
                with self.subTest(directive=directive, nested=nested):
                    _write(
                        self.root,
                        "prompts/leaf.md",
                        _prompt("shared", directive + "\n"),
                    )
                    body = "@prompts/leaf.md\n" if nested else directive + "\n"
                    _write(self.root, "prompts/root.md", _prompt("worker", body))
                    _write(self.root, "operations/example/spec.md", body)
                    _write(
                        self.root,
                        "prompts/operation-guidance/example.md",
                        '---\nname: example\ndescription: "Example"\noperation: example\n---\n'
                        + body,
                    )
                    for resolver, path in (
                        (resolve_role_prompt, "prompts/root.md"),
                        (resolve_model_instructions, "operations/example/spec.md"),
                        (
                            resolve_operation_guidance,
                            "prompts/operation-guidance/example.md",
                        ),
                    ):
                        with self.assertRaisesRegex(
                            PromptResolverError, "retired @include"
                        ):
                            resolver(self.root, path)

    @verifies("scenario.distribution.prompt-references")
    def test_invalid_targets_fail_without_expansion(self):
        for target in (
            "../outside.md",
            "/absolute.md",
            "~/home.md",
            "prompts/../leaf.md",
            "prompts//leaf.md",
            "./prompts/leaf.md",
            "prompts/leaf.txt",
            "C:/absolute.md",
            "prompts\\leaf.md",
            "prompts/missing.md",
        ):
            with self.subTest(target=target):
                _write(
                    self.root, "prompts/root.md", _prompt("worker", "@" + target + "\n")
                )
                with self.assertRaises(PromptResolverError) as failure:
                    resolve_role_prompt(self.root, "prompts/root.md")
                self.assertEqual(
                    "CONCORDE-PROMPT-MISSING-001", failure.exception.rule_id
                )

    @verifies("scenario.distribution.prompt-references")
    def test_symlink_file_and_directory_are_rejected(self):
        _write(self.root, "actual/leaf.md", _prompt("worker", "Leaf\n"))
        (self.root / "prompts").mkdir()
        (self.root / "prompts/link.md").symlink_to(self.root / "actual/leaf.md")
        (self.root / "prompts/alias").symlink_to(
            self.root / "actual", target_is_directory=True
        )
        for target in ("prompts/link.md", "prompts/alias/leaf.md"):
            with self.subTest(target=target):
                _write(
                    self.root, "prompts/root.md", _prompt("worker", "@" + target + "\n")
                )
                with self.assertRaises(PromptResolverError) as failure:
                    resolve_role_prompt(self.root, "prompts/root.md")
                self.assertEqual(
                    "CONCORDE-PROMPT-MISSING-001", failure.exception.rule_id
                )

    @verifies("scenario.distribution.prompt-references")
    def test_malformed_bindings_fail(self):
        _write(self.root, "prompts/leaf.md", _prompt("worker", "Leaf\n"))
        for arguments in ('NAME="unfinished', "bare", "NAME=a NAME=b", "9NAME=a"):
            with self.subTest(arguments=arguments):
                _write(
                    self.root,
                    "prompts/root.md",
                    _prompt("worker", "@prompts/leaf.md " + arguments + "\n"),
                )
                with self.assertRaises(PromptResolverError) as failure:
                    resolve_role_prompt(self.root, "prompts/root.md")
                self.assertEqual(
                    "CONCORDE-PROMPT-UNRESOLVED-001", failure.exception.rule_id
                )

    @verifies("scenario.distribution.prompt-references")
    def test_worker_spec_cannot_include_outside_prompts(self):
        _write(self.root, "operations/example/spec.md", "@other/leaf.md\n")
        with self.assertRaises(PromptResolverError) as failure:
            resolve_model_instructions(self.root, "operations/example/spec.md")
        self.assertEqual("CONCORDE-PROMPT-SCOPE-001", failure.exception.rule_id)

    @verifies("scenario.distribution.prompt-references")
    def test_retired_syntax_blocks_build_and_package_validation(self):
        from concorde.distribution.build import BuildError, build, write_build
        from concorde.distribution.package_validation import _validate_prompts
        from tests.concorde.support.build_fixture import build_package_copy

        build_package_copy(self.root)
        path = self.root / "prompts/operation-guidance/concorde-plan.md"
        path.write_text(path.read_text().replace("@prompts/", "@include prompts/"))
        before = (self.root / "generated/build-manifest.json").read_bytes()
        for render in (build, write_build):
            with (
                self.subTest(render=render.__name__),
                self.assertRaisesRegex(BuildError, "retired @include"),
            ):
                render(self.root)
        self.assertEqual(
            before, (self.root / "generated/build-manifest.json").read_bytes()
        )
        findings = _validate_prompts(self.root)
        self.assertTrue(
            any(
                f.rule_id == "CONCORDE-PROMPT-UNRESOLVED-001"
                and "retired @include" in f.message
                and "@path.md" in f.remediation
                for f in findings
            ),
            findings,
        )

    # --- 1. cycle -----------------------------------------------------

    def test_cycle_between_two_prompts_is_rejected(self):
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "A body\n\n@prompts/workflow-host/b.md\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/b.md",
            _prompt("worker", "B body\n\n@prompts/workflow-host/a.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-CYCLE-001")

    def test_self_cycle_is_rejected(self):
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/workflow-host/a.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-CYCLE-001")

    # --- 2. diamond: same file reached twice within one root ----------

    def test_diamond_inclusion_is_rejected_and_reports_both_paths(self):
        _write(
            self.root,
            "prompts/workflow-host/root.md",
            _prompt(
                "worker",
                "Root\n\n@prompts/workflow-host/left.md\n\n@prompts/workflow-host/right.md\n",
            ),
        )
        _write(
            self.root,
            "prompts/workflow-host/left.md",
            _prompt("worker", "Left\n\n@prompts/workflow-host/shared.md\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/right.md",
            _prompt("worker", "Right\n\n@prompts/workflow-host/shared.md\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/shared.md",
            _prompt("worker", "Shared text\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/root.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-DIAMOND-001")
        message = str(context.exception)
        self.assertIn("left.md", message)
        self.assertIn("right.md", message)

    def test_same_root_can_be_resolved_twice_without_diamond(self):
        _write(
            self.root, "prompts/workflow-host/shared.md", _prompt("worker", "Shared\n")
        )
        _write(
            self.root,
            "prompts/workflow-host/one.md",
            _prompt("worker", "One\n\n@prompts/workflow-host/shared.md\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/two.md",
            _prompt("worker", "Two\n\n@prompts/workflow-host/shared.md\n"),
        )
        one = resolve_role_prompt(self.root, "prompts/workflow-host/one.md")
        two = resolve_role_prompt(self.root, "prompts/workflow-host/two.md")
        self.assertIn("Shared", one.body)
        self.assertIn("Shared", two.body)

    # --- 3. missing target ---------------------------------------------

    def test_missing_include_target_is_rejected(self):
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/workflow-host/missing.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-MISSING-001")

    def test_unsafe_include_path_is_rejected(self):
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@../outside.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-MISSING-001")

    # --- 4. unresolved directive or variable ----------------------------

    def test_unbound_variable_is_rejected(self):
        _write(
            self.root,
            "prompts/workflow-host/leaf.md",
            _prompt("worker", "Hello {NAME}.\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/workflow-host/leaf.md\n"),
        )
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
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/workflow-host/leaf.md not-a-key-value\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-UNRESOLVED-001")

    def test_reserved_variables_pass_through_unresolved(self):
        _write(
            self.root,
            "prompts/workflow-host/leaf.md",
            _prompt("ambient", "Run `{OPERATION}` with {SCRIPT} under {FRAMEWORK}.\n"),
        )
        _write(
            self.root,
            "prompts/operation-guidance/concorde-x.md",
            '---\nname: concorde-x\ndescription: "X"\noperation: x\n---\n\n@prompts/workflow-host/leaf.md\n',
        )
        result = resolve_operation_guidance(
            self.root, "prompts/operation-guidance/concorde-x.md"
        )
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
        _write(
            self.root,
            "prompts/workflow-host/leaf.md",
            _prompt("ambient", "Ambient text\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/workflow-host/leaf.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-AUDIENCE-001")

    def test_ambient_root_cannot_include_worker_prompt(self):
        _write(
            self.root,
            "prompts/workflow-host/leaf.md",
            _prompt("worker", "Worker text\n"),
        )
        _write(
            self.root,
            "prompts/operation-guidance/concorde-x.md",
            '---\nname: concorde-x\ndescription: "X"\noperation: x\n---\n\n@prompts/workflow-host/leaf.md\n',
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_operation_guidance(
                self.root, "prompts/operation-guidance/concorde-x.md"
            )
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-AUDIENCE-001")

    def test_shared_prompt_is_includable_from_either_audience(self):
        _write(
            self.root,
            "prompts/workflow-host/leaf.md",
            _prompt("shared", "Shared text\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/workflow-host/leaf.md\n"),
        )
        _write(
            self.root,
            "prompts/operation-guidance/concorde-x.md",
            '---\nname: concorde-x\ndescription: "X"\noperation: x\n---\n\n@prompts/workflow-host/leaf.md\n',
        )
        role_result = resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        skill_result = resolve_operation_guidance(
            self.root, "prompts/operation-guidance/concorde-x.md"
        )
        self.assertIn("Shared text", role_result.body)
        self.assertIn("Shared text", skill_result.body)

    # --- 6. include of a skill source or of anything under specs/ -------

    def test_include_of_skill_source_is_rejected(self):
        _write(
            self.root,
            "prompts/operation-guidance/concorde-x.md",
            '---\nname: concorde-x\ndescription: "X"\noperation: x\n---\n\nBody\n',
        )
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/operation-guidance/concorde-x.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-SCOPE-001")

    def test_include_of_spec_document_is_rejected(self):
        _write(self.root, "specs/example/system.md", "# Example\n")
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@specs/example/system.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-SCOPE-001")

    # --- 7. crossing the prompts/protocol/ boundary ----------------------

    def test_protocol_prompt_cannot_include_outside_protocol(self):
        _write(
            self.root,
            "prompts/protocol/principles.md",
            _prompt("shared", "@prompts/workflow-host/leaf.md\n"),
        )
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("shared", "Leaf\n"))
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/protocol/principles.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-PROTOCOL-001")

    def test_non_protocol_prompt_cannot_include_protocol(self):
        _write(
            self.root,
            "prompts/protocol/principles.md",
            _prompt("shared", "Principles\n"),
        )
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@prompts/protocol/principles.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-PROTOCOL-001")

    def test_protocol_prompt_may_include_another_protocol_prompt(self):
        _write(
            self.root,
            "prompts/protocol/principles.md",
            _prompt("shared", "@prompts/protocol/kinds.md\n"),
        )
        _write(self.root, "prompts/protocol/kinds.md", _prompt("shared", "Kinds\n"))
        result = resolve_role_prompt(self.root, "prompts/protocol/principles.md")
        self.assertIn("Kinds", result.body)

    # --- 8. unreachable prompt files given a set of roots ----------------

    def test_protocol_adapter_includes_plain_standard_and_tracks_its_bytes(self):
        _write(
            self.root,
            "prompts/protocol/principles.md",
            _prompt("shared", "@protocol/principles.md\n"),
        )
        _write(
            self.root,
            "protocol/principles.md",
            "# Independent standard\n\nNo Spec declaration or prompt front matter.\n",
        )
        result = resolve_role_prompt(self.root, "prompts/protocol/principles.md")
        self.assertEqual(
            result.body, (self.root / "protocol/principles.md").read_text()
        )
        self.assertEqual(
            result.sources, ("prompts/protocol/principles.md", "protocol/principles.md")
        )

    def test_worker_prompt_cannot_import_independent_standard(self):
        _write(self.root, "protocol/principles.md", "# Standard\n")
        _write(
            self.root,
            "prompts/workflow-host/a.md",
            _prompt("worker", "@protocol/principles.md\n"),
        )
        with self.assertRaises(PromptResolverError) as context:
            resolve_role_prompt(self.root, "prompts/workflow-host/a.md")
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-PROTOCOL-001")

    def test_unreachable_prompt_is_reported(self):
        _write(
            self.root, "prompts/workflow-host/root.md", _prompt("worker", "Root only\n")
        )
        _write(
            self.root,
            "prompts/workflow-host/orphan.md",
            _prompt("worker", "Never included\n"),
        )
        unreachable = find_unreachable_prompts(
            self.root, ["prompts/workflow-host/root.md"]
        )
        self.assertEqual(unreachable, ("prompts/workflow-host/orphan.md",))
        with self.assertRaises(PromptResolverError) as context:
            check_reachability(self.root, ["prompts/workflow-host/root.md"])
        self.assertEqual(context.exception.rule_id, "CONCORDE-PROMPT-UNREACHABLE-001")

    def test_every_prompt_reachable_reports_no_gap(self):
        _write(
            self.root,
            "prompts/workflow-host/root.md",
            _prompt("worker", "@prompts/workflow-host/leaf.md\n"),
        )
        _write(self.root, "prompts/workflow-host/leaf.md", _prompt("worker", "Leaf\n"))
        unreachable = find_unreachable_prompts(
            self.root, ["prompts/workflow-host/root.md"]
        )
        self.assertEqual(unreachable, ())
        check_reachability(
            self.root, ["prompts/workflow-host/root.md"]
        )  # must not raise


if __name__ == "__main__":
    unittest.main()
