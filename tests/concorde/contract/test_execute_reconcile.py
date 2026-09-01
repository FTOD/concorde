import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


COMMANDS = REPOSITORY_ROOT / "presets/concorde/commands"
WORKFLOW_CONTRACT = (
    REPOSITORY_ROOT
    / "specs/concorde/features/001-concorde-workflow/contracts/agent-commands.md"
)


class ExecuteReconcileContractTests(unittest.TestCase):
    def command(self, name: str) -> str:
        return (COMMANDS / f"speckit.{name}.md").read_text(encoding="utf-8")

    def test_all_surfaces_use_full_selected_and_parent_workspace_authority(self):
        for name in ("implement", "analyze", "converge"):
            content = " ".join(self.command(name).split())
            for invariant in (
                "workspace.feature_abstract",
                "workspace.feature_design",
                "workspace.feature_implementation",
                "parent_context.feature_abstract",
                "parent_context.feature_design",
                "parent_context.feature_implementation",
                "workspace.module_summary",
                "workspace.module_design",
                "sibling design/implementation body",
                "parent/sibling `attempt/`",
            ):
                self.assertIn(invariant, content, f"{name}: {invariant}")

    def test_implementation_requires_persisted_evidence_before_completion(self):
        content = " ".join(self.command("implement").split())
        for invariant in (
            "Evidence before completion",
            "ATTEMPT_DIR/validation.md",
            "verification command or check",
            "outcome",
            "relevant artifact",
            "limitation",
            "MUST remain unchecked",
            "protected-authority",
            "SHA-256",
            "failed verification",
            "setup-file inspection as read-only by default",
            "one dependency-ready executable task",
            "stable task ID",
            "requirement, acceptance-outcome, or named plan-section trace token",
            "detected tool",
            "exact project-relative setup file being changed",
            "action authorizing the required creation or edit",
            "cannot independently authorize a setup mutation",
            "Repository/tool detection alone MUST NOT authorize a write",
            "preserve every setup file byte-for-byte",
            "Never synthesize authorization from repository detection",
        ):
            self.assertIn(invariant, content, invariant)

    def test_analysis_has_five_categories_and_one_file_mutation_budget(self):
        content = " ".join(self.command("analyze").split())
        for invariant in (
            "READ-ONLY EXCEPT REFLECTION RECORDING",
            "absent evidence",
            "disagreement",
            "ambiguity",
            "duplication",
            "coverage gap",
            "prevailing `design.md` requirement",
            "workspace.reflections",
            "no recordable problem MUST make zero filesystem changes",
            "Every other file MUST remain byte-identical",
        ):
            self.assertIn(invariant, content, invariant)

    def test_convergence_is_verified_deduplicating_and_append_only(self):
        content = " ".join(self.command("converge").split())
        for invariant in (
            "APPEND-ONLY, NEVER REWRITE",
            "Attempt Evidence",
            "semantic duplicate",
            "preserve completed tasks",
            "next phase number",
            "byte-for-byte unchanged",
            "no empty Convergence header",
            "workspace.reflections",
            "implementation-owned diagram source/evidence",
            "missing required diagram declaration",
            "incorrect core role/kind",
            "prose/contract authority disagreement",
            "specification or architecture review",
            "never append a task that edits feature `design.md`",
            "maintained JSON that is already authorized, validation, delivery, automatic embedding",
            "truthful visual-review evidence, and freshness",
        ):
            self.assertIn(invariant, content, invariant)
        self.assertNotIn(
            "Append work for `diagrams/` placement, declaration in `design.md`, maintained Archify "
            "JSON, prose alignment, contract references, delivery, automatic feature-page "
            "embedding, truthful visual-review evidence, and freshness",
            content,
        )

    def test_shared_contract_defines_execute_and_reconcile_handoff(self):
        content = " ".join(WORKFLOW_CONTRACT.read_text(encoding="utf-8").split())
        for invariant in (
            "Execute and Reconcile Handoff",
            "Implementation execution",
            "Attempt evidence",
            "Analysis result",
            "Convergence result",
            "Failed verification",
            "reflection-log-only",
            "append-only",
            "byte-identical",
        ):
            self.assertIn(invariant, content, invariant)


if __name__ == "__main__":
    unittest.main()
