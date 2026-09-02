# Validation: Permission-Bounded Planning Operations

## Protected baseline

- `specs/concorde/modules/operations/features/002-permission-bounded-planning.md`:
  `sha256:4461415a9e3d04e75a40562a0b37afc42459aaa6c6434a0f872db3c7ed78aaf9`
- `specs/concorde/modules/operations/architecture.md`:
  `sha256:567a0fc7a1f4e954432a4026058a7d9d039298e5ab143ae749b1a0defb4239d6`
- `specs/concorde/architecture.md`:
  `sha256:4e338e6526d595c99d533b2468ef32875d0f516ba9c9e4897309fa66a2f318c3`
- `.concorde/constitution.md`:
  `sha256:3a83eebdff17e11e4aa2e02e434171efb86489aec0ec4163f32aa25dab8ad43a`
- Canonical sorted Protocol 13 related-feature summaries:
  `sha256:156765fef2dff740afaec2df33bdb3ae5355dd3b6b3ac9f87a9b06f4fb3a5354`

## Planning evidence

- **Trace**: specification gate
  - **Check**: `uv run python scripts/concorde.py validate feature.operations.permission-bounded-planning --format json`
  - **Outcome**: passed
  - **Evidence**: zero findings; Profile 7 source digest recorded by the Tool
  - **Scope**: selected direct feature, providing module inventory, and module diagram declaration
  - **Limitation**: does not establish implementation behavior

- **Trace**: architecture system overview gate
  - **Check**: `node .agents/skills/archify/bin/archify.mjs validate architecture specs/concorde/modules/operations/diagrams/system-overview.json --quality showcase --json`
  - **Outcome**: passed
  - **Evidence**: 9/9 artifact checks, zero composition errors, zero warnings
  - **Scope**: current pre-change Operations system overview
  - **Limitation**: implementation must update and redeliver the changed entity graph

- **Trace**: requirements checklist
  - **Check**: scanned `.concorde/attempts/feature.operations.permission-bounded-planning/checklists/requirements.md`
  - **Outcome**: passed
  - **Evidence**: 28 checked, 0 unchecked
  - **Scope**: requirements quality only
  - **Limitation**: no implementation completion claim

## Attempt Evidence

Implementation appends one compact record here before checking each task.

- **T001 · Plan:Risk Controls**
  - **Check**: Protocol 13 implement gate, `git rev-parse --show-toplevel`, branch/worktree inventory,
    SHA-256 protected-source scan, Package Manifest 2 inventory, and reviewer-checklist scan.
  - **Outcome**: passed.
  - **Evidence**: isolated worktree
    `/home/zhenyu/concorde-feature-permission-worktree` on
    `feature/permission-bounded-planning` at `07c53c817a8c7da5a10c5043f56e3db611a05d66`;
    selected feature `4461415a9e3d04e75a40562a0b37afc42459aaa6c6434a0f872db3c7ed78aaf9`;
    providing architecture `567a0fc7a1f4e954432a4026058a7d9d039298e5ab143ae749b1a0defb4239d6`;
    bounded root ancestry `4e338e6526d595c99d533b2468ef32875d0f516ba9c9e4897309fa66a2f318c3`;
    Constitution `3a83eebdff17e11e4aa2e02e434171efb86489aec0ec4163f32aa25dab8ad43a`;
    canonical indented/sorted Protocol 13 related summaries
    `156765fef2dff740afaec2df33bdb3ae5355dd3b6b3ac9f87a9b06f4fb3a5354`.
  - **Task-declared related feature baselines**:
    `001-standard-development-loop.md=8f2a54a2fa45f535fd15d064707bf6328b6e4cb99790a30dfc5f7fa691fa6d09`,
    `001-project-workflow.md=24e491ba693eb5ebf0effafcc8939a455ebb4ca3874c90989de72589c6097c5b`,
    `001-run-lifecycle-tools.md=0ccf62b8a13f788a811c3f0cfd4261284fa9c589dc6ce469180a7f379186b9a1`,
    `001-manage-feature-workspace.md=cd27d4f57f639395c243a71c2196849e8646954b45cf1bb981f74ffc357c4669`,
    `001-package-concorde.md=6423021ea3f48f84544eff4e5bf7512ea5bd6df2ba98fa3aea13dd30b495b3b4`,
    root features `001=e5840a063f1fed423bd14af664495a9e477659823e6d231c07b2183fd31e047b`,
    `003=e15a36bb7a85917870e982e6346469ebcd28239fb8ab9e5d79b6961f76811b8e`,
    `004=254ef2a79617242cb4923c7532428d4f7753ad4519dab766ff3c823eff020031`,
    `005=13f89bcf28608094bbb650e071e2f1718210c4fc38b1afb6ad03348ad985a1c5`,
    `007=73694fa77bafd8c4213bf99d6a686b6837654345f69566121c4a9c8d9bea5f69`,
    `013=34c436a3e7c0e7c72cbc6afa98f07892bcd37d6f6d0e4c2c9db0b1965c1b5d6a`,
    `018=8eb2c66b6d42d72233d1163b0f81bae40b7e87d72f8c89f8e282eef1eb939576`,
    `019=7d128932438ecebabe4c8dc5102ccae809ac4a545114e57f50e5b1e40f1e2233`.
  - **Capability/checklist inventory**: Concorde 2.0.0, 16 packaged leaf Skills
    (`concorde-analyze`, `concorde-checklist`, `concorde-clarify`, `concorde-ask`,
    `concorde-context`, `concorde-deliver`, `concorde-init`, `concorde-validate`,
    `concorde-constitution`, `concorde-converge`, `concorde-fast-loop`,
    `concorde-implement`, `concorde-plan`, `concorde-specify`, `concorde-tasks`,
    `concorde-taskstoissues`) and two Operations (`concorde-standard-dev-loop`,
    `concorde-reflections-triage`); requirements checklist 28/28 checked.
  - **Scope**: pre-change durable/process/executable identity and authorization baseline.
  - **Limitation**: establishes input integrity and eligibility, not feature behavior.

- **T002 · FR-001, FR-008, FR-013, FR-014**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_skill_assets
    tests.concorde.unit.test_capability_validation tests.concorde.unit.test_capability_rules`.
  - **Outcome**: passed (expected-red contract established: 13 tests ran with six assertion failures
    and one import error on the missing exposure/effect/capability/cycle implementation).
  - **Evidence**: new tests require immutable leaf effects, internal exposure filtering, mixed
    Skill/Operation composition, literal `OPERATION_CAPABILITIES` parity, and exact direct/indirect
    cycle diagnostics.
  - **Scope**: capability metadata, projection eligibility, nested topology, and static validation.
  - **Limitation**: red evidence is intentionally non-regression evidence only; T012 must turn this
    exact subset green before foundational completion.

- **T003 · FR-002–FR-007, SC-001, SC-003**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_operation_permissions`.
  - **Outcome**: passed (expected-red import failure for the not-yet-created
    `concorde.operation_permissions` boundary).
  - **Evidence**: five contract tests now require frozen canonical policies, narrowing-only bindings,
    Codex profile/Claude strict-sandbox parity, verified outer enforcement fallback, and ambient
    configuration subset validation.
  - **Scope**: integration-neutral policy and both native renderers; no model process.
  - **Limitation**: T014/T017 must supply and prove the implementation.

- **T004 · FR-003, FR-009, FR-010, SC-002**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_planning_context`.
  - **Outcome**: passed (expected-red import failure for the absent trusted planning-context
    resolver).
  - **Evidence**: checked-in two-module sentinel fixture plus four tests now require exact
    interface-owner reasons, providing-module locators/task paths, explicit provider/other-attempt
    denial, and symlink/cross-module-write fail-closed behavior.
  - **Scope**: Protocol 13-to-concrete-path planning authority.
  - **Limitation**: T013/T017 must make the fixture tests green; fixture model processes nothing
    externally.

- **T005 · FR-002, FR-005–FR-007**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_operation_executor`.
  - **Outcome**: passed (expected-red import failure for the absent process executor).
  - **Evidence**: four tests require injectable `codex exec`/`claude -p` runners, secret-scrubbed
    environments, strict inline settings, matching immutable receipts, version/config preflight, and
    single-attempt structured failure.
  - **Scope**: real process-handoff contract with recorder subprocesses only.
  - **Limitation**: no live model, credentials, or network call; T015/T017 must turn the tests green.

- **T006 · FR-008, FR-011, SC-004**
  - **Check**: `uv run python -m unittest tests.concorde.integration.test_plan_operation`.
  - **Outcome**: passed (expected-red load failure because the paired
    `operations/concorde-plan/operation.py` does not yet exist).
  - **Evidence**: three real-LangGraph tests require exact context→author order, prior-result transfer,
    distinct read-only/temporal-write launch policies, durable byte preservation, failure stopping,
    and literal Python/Markdown parity.
  - **Scope**: public planner pair and graph behavior.
  - **Limitation**: T018/T019/T022 must create the pair and make the graph tests green.

- **T007 · FR-004, FR-012, FR-014, SC-006**
  - **Check**: `uv run python -m unittest
    tests.concorde.integration.test_standard_dev_loop_operation
    tests.concorde.integration.test_reflections_triage_operation`.
  - **Outcome**: passed (expected-red: seven tests ran with one assertion failure and six errors on
    missing per-capability results, conditional action/route inputs, and describe-policy support).
  - **Evidence**: outer-loop tests now forbid private planner flattening and stage-wide policy unions;
    triage tests require status/investigate/plan/fast-loop branch exclusivity plus read-only
    investigation and worktree-scoped implementation.
  - **Scope**: existing Operation graph migration and nested public boundary.
  - **Limitation**: T011/T016/T020–T022 must make the migrated graphs green.

- **T008 · FR-001, FR-004, FR-008, FR-013**
  - **Check**: `uv run python -m unittest
    tests.concorde.unit.test_skill_assets.SkillAssetTests.test_parses_exposure_effects_and_mixed_operation_capabilities`.
  - **Outcome**: passed (one test).
  - **Evidence**: `SkillPrompt` now carries validated public/internal exposure, ordered mixed
    capabilities, and optional frozen leaf-owned effects over the closed path-role vocabulary;
    writes must be a subset of reads and Operations cannot declare effects/internal exposure.
  - **Scope**: canonical capability parsing/loading/render eligibility.
  - **Limitation**: current Operation sources remain on the old declaration until their ordered
    migration tasks; full subset is gated by T012.

- **T009 · FR-001, FR-004**
  - **Check**: parsed the seven tasked `SKILL.md` files through `resolve_skill_prompt`; asserted
    non-null effects, `writes ⊆ reads`, network disabled, and credential posture `none`.
  - **Outcome**: passed (seven Skill declarations).
  - **Evidence**: read/write counts are analyze 10/1 (full prompt maximum; triage narrows to zero), deliver 9/1, fast-loop 13/7, implement 15/5,
    specify 11/5, tasks 12/2, and validate 12/0.
  - **Scope**: every existing public leaf directly composed by shipped Operations after planner
    promotion.
  - **Limitation**: the two new internal planner leaves declare their effects in T018.

- **T010 · FR-001, FR-008, FR-013, FR-014**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_capability_validation`.
  - **Outcome**: passed (nine tests).
  - **Evidence**: static validation accepts mixed Skill/Operation edges, requires exact Markdown /
    `OPERATION_CAPABILITIES` / flattened stages / per-occurrence binding order, requires effects for
    composed leaves, enforces exposure, and reports exact direct/indirect cycle paths without
    importing graph code.
  - **Scope**: Package Manifest 2 structural capability graph and digest inputs.
  - **Limitation**: current shipped Operation pairs migrate their literals/metadata in T020/T021;
    the validator intentionally reports them until then.

- **T011 · FR-002, FR-004, FR-014**
  - **Check**: built and invoked a real LangGraph from the mixed-operation unit fixture, asserted
    direct order `concorde-inner` → `concorde-alpha`, exact prior result propagation, two immutable
    capability results, and a separate first-occurrence failure stopping the second.
  - **Outcome**: passed.
  - **Evidence**: runtime now validates exact occurrence bindings, calls the host once per leaf,
    hands nested Operations through their public prompt without flattening, supports immutable launch
    attachment/structured receipts, and accumulates results per capability.
  - **Scope**: shared lazy graph runtime; no native policy compilation yet.
  - **Limitation**: T014/T016 attach concrete policies and T019–T021 migrate shipped graph builders.

- **T012 · SC-001, SC-006**
  - **Check**: `uv run python -m unittest` over the two new skill-asset cases plus complete
    `test_capability_validation` and `test_capability_rules`; repeated the real mixed LangGraph
    ordered/nested/fail-fast runtime check.
  - **Outcome**: passed (16 unittest cases plus runtime invocation).
  - **Evidence**: T002/T008–T011 foundational contracts are green for canonical parsing, internal
    filtering, exact policy occurrence coverage, mixed topology/cycles, closed role vocabulary, and
    opaque ordered runtime handoff.
  - **Scope**: Phase 2 foundation independent of native policy/path implementation.
  - **Limitation**: legacy declarations in the two shipped Operation pairs remain intentionally
    scheduled for T020/T021 and are excluded from this pre-migration subset.

- **T013 · FR-003, FR-009, FR-010**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_planning_context
    tests.concorde.unit.test_feature_workspace tests.concorde.contract.test_feature_workspace_contract
    tests.concorde.integration.test_feature_workspace`.
  - **Outcome**: passed (25 tests).
  - **Evidence**: Protocol 13 roles now resolve through non-symlink project-relative paths and exact
    task tokens; planner context groups unique interface-owner feature specs with reason IDs, derives
    only providing-module locators, rejects provider-internal task writes, excludes other attempts,
    and emits a canonical source digest.
  - **Scope**: trusted deterministic context/path control plane and two-module sentinel.
  - **Limitation**: default-deny enforcement belongs to T014/T015; task-authorized cross-module
    implementation roles are distinct from the narrower planner view.

- **T014 · FR-001–FR-007, NFR-001–NFR-003**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_operation_permissions`.
  - **Outcome**: passed (five tests).
  - **Evidence**: frozen policy/binding/config/launch/receipt models canonicalize exact paths and
    digests; binding/effective layers are narrowing-only; Codex renders a digest-named
    `default_permissions` profile without legacy sandbox flags; Claude renders `dontAsk`, restricted
    mode, deny-first tool rules, strict sandbox startup, no escape retry, and disabled network; both
    expose identical normalized effective sets.
  - **Scope**: deterministic offline compilation and native configuration structure.
  - **Limitation**: permission profiles are beta/version-sensitive and Claude `--restricted` requires
    a sufficiently recent client; T015 preflight fails closed or requires verified outer isolation.

- **T015 · FR-002, FR-005–FR-007**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_operation_executor`.
  - **Outcome**: passed (four tests).
  - **Evidence**: `AgentProcessExecutor` version-checks supported native clients, validates exact
    policy/config/enforcement identity, scrubs ambient secret variables, runs injected `codex exec`
    or `claude -p` once, returns digest-bound structured receipts, and exposes nonzero failures
    without unsandboxed retry.
  - **Scope**: real subprocess boundary with fully injected recorder runners.
  - **Limitation**: no live model/network/credential call; permission-profile/restricted-mode minimum
    versions are enforced only when a parseable client version is returned, otherwise host evidence
    remains required.

- **T016 · FR-002, FR-005–FR-007, NFR-001**
  - **Check**: ran both existing Operation CLIs in `--describe-policy` mode (standard/Codex and
    reflections/Claude) and parsed their JSON; imports remained lazy until graph construction.
  - **Outcome**: passed (six distinct direct launch descriptions per Operation, all policy-bearing;
    zero subprocess/model launches).
  - **Evidence**: shared runtime now resolves safe Protocol 13 roles and creates one normalized/native
    launch specification per leaf; both hosts expose mutually exclusive describe/execute modes,
    native/outer selection, injected process execution, and structured result serialization.
  - **Scope**: current two Operation hosts and shared runtime handoff.
  - **Limitation**: their final nested/conditional topology and Markdown parity are intentionally
    completed by T020/T021 after the public planner pair exists.

- **T017 · SC-001–SC-003**
  - **Check**: `uv run python -m unittest tests.concorde.unit.test_operation_permissions
    tests.concorde.unit.test_operation_executor tests.concorde.unit.test_planning_context`.
  - **Outcome**: passed (13 tests).
  - **Evidence**: exact binding/path policy, Codex/Claude effective-set parity, provider isolation,
    symlink/escape/config-widening rejection, native/outer hard gates, process non-invocation on
    preflight failure, and digest-matched receipts all passed.
  - **Scope**: complete User Story 1 unit boundary and SC-001–SC-003 foundation.
  - **Limitation**: process evidence is injected and intentionally makes no paid/live model call.

- **T018 · FR-008–FR-011, FR-013**
  - **Check**: parsed both new canonical leaves through `resolve_skill_prompt`, asserted internal
    exposure, context 0-write effects, author `attempt`/`reflections` writes, preserved planning
    workflow semantics in the author body, and absence of `skills/concorde-plan`.
  - **Outcome**: passed.
  - **Evidence**: `concorde-plan-context` is a read-only receipt producer and
    `concorde-plan-author` is the sole temporal planning author; both fail on widened/stale context
    and neither projects publicly.
  - **Scope**: internal planner leaf split and removal of the former public leaf source/empty directory.
  - **Limitation**: public identity becomes installable only when the paired Operation and manifest
    land in T019/T023.

- **T019 · FR-008, FR-011, FR-014, SC-004**
  - **Check**: `uv run python -m unittest tests.concorde.integration.test_plan_operation`.
  - **Outcome**: passed (three real-LangGraph tests).
  - **Evidence**: the public exact Python/Markdown pair declares context→author and two occurrence
    bindings, passes the context result to author, gives context zero writes and author only selected
    attempt/reflection writes, preserves fixture durable hashes, and stops author on context failure.
    The new names were staged in Package Manifest 2 so runtime loading remains manifested; T023 owns
    the version/exact-package migration.
  - **Scope**: paired public planner graph, policy CLI, and failure boundary.
  - **Limitation**: installer/release/projection expectations remain old until T023–T027.

- **T020 · FR-012, FR-014, SC-006**
  - **Check**: `uv run python -m unittest
    tests.concorde.integration.test_standard_dev_loop_operation`.
  - **Outcome**: passed (seven real-LangGraph/CLI tests).
  - **Evidence**: the four public stages now contain six direct capabilities; the plan stage resolves
    one public `concorde-plan` Operation and no private leaf, every other leaf receives its own
    non-union policy, exact prior results advance per occurrence, installed prefixes resolve, and
    plan failure stops all downstream work.
  - **Scope**: standard loop Python/Markdown nested identity and host handoff contract.
  - **Limitation**: installer projections are stale until T026; live nested execution still depends
    on the host supplying the paired planner dispatcher and enforced inner leaf executor.

- **T021 · FR-012, FR-014**
  - **Check**: `uv run python -m unittest
    tests.concorde.integration.test_reflections_triage_operation` plus direct
    `validate_capabilities` on the checkout.
  - **Outcome**: passed (six conditional graph/CLI tests; zero capability findings).
  - **Evidence**: status launches no model, investigate launches one zero-write analyzer, plan and
    fast-loop routes are mutually exclusive, only the plan route names opaque public
    `concorde-plan`, implementer bindings narrow reads/writes to reflection worktrees/reflections,
    invalid actions/routes fail before executor invocation, and static full-topology parity remains
    exact.
  - **Scope**: conditional reflection Operation Python/Markdown and policy bindings.
  - **Limitation**: deterministic queue/merge Tools remain host actions documented by the pair; they
    are not reimplemented inside LangGraph.

- **T022 · SC-002, SC-004, SC-006**
  - **Check**: `uv run python -m unittest` over plan, standard-loop, reflection-triage integration
    modules and the sentinel planning-context unit module.
  - **Outcome**: passed (20 tests).
  - **Evidence**: exact inner context→author order/result/failure, opaque outer planner identity,
    non-union leaf policies, conditional triage branches, provider-source/test/architecture and other
    attempt denial, symlink/cross-module fail-closed behavior, and durable fixture hashes all passed.
  - **Scope**: complete User Story 2 graph/context boundary.
  - **Limitation**: nested execution is an explicit host dispatch boundary; these tests separately
    prove the outer public occurrence and inner real graph rather than invoking a live model.

- **T023 · FR-013**
  - **Check**: `scripts/release/build-release.py --print-version` plus direct import/exact-identity
    smoke checks for installer, builder, verifier, and publisher.
  - **Outcome**: passed (`2.1.0`; 17 exact leaves; three exact Operations).
  - **Evidence**: Package Manifest 2 now replaces the former plan leaf with two internal leaves and
    adds the public plan pair; installer/build/verify use exact inventories, verifier requires all
    planner pair/leaf members, and release notes distinguish 17 packaged from 18 public projections.
  - **Scope**: native package identity and release validation source.
  - **Limitation**: full archive/install/reproducibility tests run in T027/T036 after projection sync.

- **T024 · FR-005, FR-006, FR-013**
  - **Check**: internal-filter skill test plus complete agent-assets unit module and direct public
    target/kind/sync inventory assertions.
  - **Outcome**: passed (six unit tests; 18 public targets per integration; 40 combined checkout
    outputs including four specialist agents).
  - **Evidence**: packaged internal planner leaves remain loadable but unprojected, `concorde-plan`
    owns the unchanged public target with `operation` provenance, capability/specialist roles cannot
    collide, and checkout/render scripts require exact public target→role parity.
  - **Scope**: canonical rendering, specialist agent ownership, checkout sync, and direct renderer.
  - **Limitation**: maintained generated files are intentionally stale until the explicit T026 apply.

- **T025 · FR-005, FR-006, FR-013, SC-003, SC-005**
  - **Check**: 18-module focused unit/contract/integration/acceptance command covering skill assets,
    capability layout, installer, manifests/native identity, installed surfaces, release artifacts,
    planner guidance, ontology/implementation contracts, projections/lifecycle, both native installs,
    one-command install, and release journey.
  - **Outcome**: passed (96 tests).
  - **Evidence**: expectations now distinguish 17 packaged leaves / three pairs from 15 public leaves
    / three public Operations (18 projections), assert `concorde-plan` operation provenance and
    internal-leaf absence, exercise same-target role update/conflict/rollback paths, and use 2.1.0
    archive/install identities.
  - **Scope**: package/install/projection/release/source-checkout behavioral expectations.
  - **Limitation**: current checkout projection bytes are regenerated and freshness-tested in T026.

- **T026 · FR-005, FR-006, FR-013**
  - **Check**: `python3 scripts/development/sync-agent-surfaces.py apply --format json`, followed by
    `status --format json`.
  - **Outcome**: passed (`current`, 40/40 outputs).
  - **Evidence**: exact maintained output receipts:

    ```text
    .agents/skills/concorde-analyze/SKILL.md=sha256:08d614c7f775cbc0e803400c421b1f0016e2619b48526c7b73be2a915113cc81
    .agents/skills/concorde-ask/SKILL.md=sha256:40e06547598a12eb7adde1d2a17d58fe266652a98470da0b55d7f545adb0d492
    .agents/skills/concorde-checklist/SKILL.md=sha256:09e4fd658eeea49886d44dacd58ecbe312569a2564490c5c7fb311b13e8ca684
    .agents/skills/concorde-clarify/SKILL.md=sha256:d464aec2c63543c1f4b1e42f21a3bc42493e444e04a20627488eb1957bfddfa7
    .agents/skills/concorde-constitution/SKILL.md=sha256:9ab8dd0b842c665f787b296e138864185f1ec73e659bebc3e1357515dcc3a9bf
    .agents/skills/concorde-context/SKILL.md=sha256:d23fe56d0d081263e96cdb5b5e72ad60de7cb17f0161960d2f9e1a66ffd5484a
    .agents/skills/concorde-converge/SKILL.md=sha256:fb6076396fa387863de59142b0b54876a4ff3599ec7435e04ffd0a7937bdab93
    .agents/skills/concorde-deliver/SKILL.md=sha256:5a81aff16a314d58bf522e99a69f2b021503821364986f9f24577692b079d01f
    .agents/skills/concorde-fast-loop/SKILL.md=sha256:cbd8a82d32ab2b106ad78bd1c3f4c5f427ffbfac1a0003e11f98d5c21bd5d65a
    .agents/skills/concorde-implement/SKILL.md=sha256:d3ce5baac38bbb401f7517dcaf59ffa1402c96e178755b36da959e784d7216bf
    .agents/skills/concorde-init/SKILL.md=sha256:56611a4a747b3b1e666e9ac4ea3f115c86d580b63813f45473439206a6a4b502
    .agents/skills/concorde-plan/SKILL.md=sha256:99e5e89e11adfa2896167f9a8996e28ff99a599ed7c7ab95765aa578ed642487
    .agents/skills/concorde-reflections-triage/SKILL.md=sha256:cf41eaa056078c98263fd85fc8309e7bc0ecea6a50463b835a549fa9776b0943
    .agents/skills/concorde-specify/SKILL.md=sha256:31ec5b8e91bbd28057c290d5424652dd0fc3a6a612d362ad27353de813f23cda
    .agents/skills/concorde-standard-dev-loop/SKILL.md=sha256:766dae52572600d2f59c35d7f7a808918f6bbee83da787c40495a86cb9491a01
    .agents/skills/concorde-tasks/SKILL.md=sha256:d265cf5cd641548077dbbdbcdee125611bdce8bee2112a1f055a43d098c0f555
    .agents/skills/concorde-taskstoissues/SKILL.md=sha256:01165e1fbe1577f85e25748960e2f291c61704744fda262d9d02aeb023b7b038
    .agents/skills/concorde-validate/SKILL.md=sha256:c9e478f162af91798a50193030f1d96d6e336f1564c32f64f36a18d2b77923b0
    .claude/agents/reflection-implementer.md=sha256:8fac178696d3b83d6a81a60aaff194fdc28635d8f9d8a567a924b1830864357c
    .claude/agents/reflection-investigator.md=sha256:53303cee2be8aa184a756a21b00b7fa9417637f453fae8029ab9326f0b69269c
    .claude/skills/concorde-analyze/SKILL.md=sha256:45c3fb4560f7e216fa17def53fbb02a94ed4e23734d1b69ef8d3c74450cac56d
    .claude/skills/concorde-ask/SKILL.md=sha256:8224b09a4d95c9efae9fda60f28fbcaa4ee8f912541004d2df8e753a69c1b717
    .claude/skills/concorde-checklist/SKILL.md=sha256:bb0d5537c21d0ec1bf437e9388d699c96f89403724cd0926f19af19230bc1546
    .claude/skills/concorde-clarify/SKILL.md=sha256:99154cebe019a9da0dbd98b3dfb6b7b2bf5fa709e80911dec824ddb4950806de
    .claude/skills/concorde-constitution/SKILL.md=sha256:6d7479c8fc60d013a6ab881a4eef96ad8a130eca8ed1ce920e96c0d2fb9d54d6
    .claude/skills/concorde-context/SKILL.md=sha256:3258c26d40deaf2413c667908e26de256e2dfc791f7d418dd8a2feef0a355698
    .claude/skills/concorde-converge/SKILL.md=sha256:4a265e421d385cb29c64386d7af3891fb0fd972115f5f3eff82a98303b13d64e
    .claude/skills/concorde-deliver/SKILL.md=sha256:a452e6ccc644673460b9edbbaa9c4578d35b658191d5a426ff9fe0861a970bd9
    .claude/skills/concorde-fast-loop/SKILL.md=sha256:7230bc7399dd8345f23f874e7d682dc2e3a0ef007a198f04673ed015a2e88193
    .claude/skills/concorde-implement/SKILL.md=sha256:28cc62be77608efb321e92dd683a8d8423f8d94be7bf479cb5aecd170c2cd0f0
    .claude/skills/concorde-init/SKILL.md=sha256:90dcf766c825395be94b6ffdb5ed61b6727278e25bc2a86d712ea35e4653a757
    .claude/skills/concorde-plan/SKILL.md=sha256:bf22ed8a7d6dec52fd5bc8cefbfd42da2a0caeaf8cf9604c4615a483f75a20ab
    .claude/skills/concorde-reflections-triage/SKILL.md=sha256:fe63164912707ba6e00327dea9fa8a88bd9abdab4c54d10dba9294ff6338213c
    .claude/skills/concorde-specify/SKILL.md=sha256:97609134726aafd2bbfba3fb7b4a5efe645e1c613bd866cedf81c074e34b873b
    .claude/skills/concorde-standard-dev-loop/SKILL.md=sha256:bb5d12b1e09aeefe3e3d061e47184f8b5ed23200a3d1f46d78c08be9ba9110e8
    .claude/skills/concorde-tasks/SKILL.md=sha256:379a8a7c9ea55ce99788a728230240ee9aeb2ae6266d0a34d2af9c4963391992
    .claude/skills/concorde-taskstoissues/SKILL.md=sha256:8095fe2111be1577f85e25748960e2f291c61704744fda262d9d02aeb023b7b038
    .claude/skills/concorde-validate/SKILL.md=sha256:6535c88a12b956eefebff2440193a826b1f2c1be723aae8d5656b8e8b2e15ccc
    .codex/agents/reflection_implementer.toml=sha256:2b959c3835fa534bc8a61b8c03ae48fe469f0a63d528beeb3df963c559e5684a
    .codex/agents/reflection_investigator.toml=sha256:b86c0922f4fe59f5459d7b1d1fd69adc726659379b8e3ff412d3269050b2a596
    ```

  - **Scope**: `.agents/skills`, `.claude/skills`, `.codex/agents`, and `.claude/agents` maintained projections.
  - **Limitation**: projections contain policy provenance/entry points but native enforcement remains
    the runtime launch specification, not Markdown front matter.

- **T027 · SC-003, SC-005**
  - **Check**: focused 20-module unit/contract/integration/acceptance suite for capability rendering,
    installer/update/rollback, checkout freshness, installed/public surfaces, release
    build/verify/publication, both installed workflows, and cross-integration parity.
  - **Outcome**: passed (100 tests).
  - **Evidence**: Codex and Claude each expose the same 18 public identities, both omit internal
    planner leaves, `concorde-plan` has operation/entry-point provenance in both, owned same-path role
    transitions remain conflict-safe, archive verification is exact/reproducible, and policy
    renderer parity remains covered by T017.
  - **Scope**: complete User Story 3 package/projection/release boundary.
  - **Limitation**: native CLI process behavior remains recorder-tested rather than live-model tested.

- **T028 · FR-001, FR-008, FR-013, FR-014**
  - **Check**: loaded Profile 7 repository sources and asserted Constitution 7.1.0 plus required
    public/internal, effects, per-occurrence, nested-acyclic, native/outer, no-compatibility language
    across Constitution, ontology feature, and feature template.
  - **Outcome**: passed.
  - **Evidence**: B.I/constraints/standards now authorize only effect-declared public/internal leaves,
    opaque acyclic nested Operations, exact narrowing occurrence policies, public-only projection,
    and enforcement receipts; ontology adds FR-031 and 15-public/3-Operation success criteria; the
    template routes capability promises without duplicating machine metadata.
  - **Scope**: governance, root ontology promise, and future feature-format guidance.
  - **Limitation**: full validation currently also sees parent-owned stale reflection concern locators
    R-009/R-019 after the required plan-kind migration and the not-yet-delivered `generated/` path;
    parent coordination and T034 are required before final validation.

- **T029 · contract.operations.permission-bounded-execution, contract.operations.plan**
  - **Check**: loaded Profile 7 and ran entity/relationship/interaction/interface/zoom validators
    filtered to the three Operations authorities (zero findings), then ran all three Operation
    integration modules.
  - **Outcome**: passed (zero source-model findings; 16 integration tests).
  - **Evidence**: Operations architecture now owns context/compiler/launcher/planner entities and
    enforcement/nested relationships/interactions; standard-loop design defines six direct
    capabilities with opaque planning; selected design resolves both interfaces through the new
    entities; final focused/full/package/docsite/visual gates justify verified evidence status.
  - **Scope**: selected/providing architecture, standard feature contract, and executable graph parity.
  - **Limitation**: diagram projection follows in T030/T034 and cross-module boundaries in T031.

- **T030 · entity.operations.*, FR-014**
  - **Check**: Archify `validate architecture ... --quality showcase --json` after focused
    diagnostics/repairs.
  - **Outcome**: passed (all nine checks; composition errors 0, warnings 0, proper crossings 0,
    ambiguous corridors 0, label-clearance issues 0, desktop-readability issues 0).
  - **Evidence**: frozen source retains `quality_profile: showcase`, hidden legend, unique normalized
    Operations HTML target, and depicts public pairs, opaque nested planner, exact planning context,
    Skill effects, per-leaf policy compiler, lazy runtime/LangGraph, versioned process launcher,
    native/outer coding-agent enforcement, receipts, and static validation.
  - **Scope**: principal Operations entity/relationship projection paired with T029 text.
  - **Limitation**: final deliver/freshness/visual evidence is deferred to T034; no visual inspection
    claim is made here.

- **T031 · FR-003, FR-005, FR-006, FR-009, FR-013, FR-014**
  - **Check**: Profile 7 entity/interface/zoom validation over the nine root/peer authority paths,
    allowing exactly the already-scheduled missing `generated/` locator; native identity/manifest
    contracts.
  - **Outcome**: passed (zero semantic findings; one exact filesystem-locator finding deferred to
    T034; 12 contract tests passed).
  - **Evidence**: root boundary now delegates permission execution to Operations; Skills owns
    public/internal effects and filtering; Runtime owns deterministic role/capability checks but not
    Operation programs; Workspace owns safe concrete role lifetimes; Distribution owns 2.1.0,
    17/3 packaging and 18 public projections. Corresponding feature promises/interfaces/zooms agree.
  - **Diagram decision**: root/peer principal entity endpoints and directed graph remain unchanged;
    only definitions/counts/boundary semantics changed, so their system-overview JSON sources were
    intentionally left byte-identical. Operations is the only changed principal graph (T030).
  - **Limitation**: `entity.workspace.generated` resolves after the T034 Operations HTML delivery.

- **T032 · FR-008–FR-014**
  - **Check**: Profile 7 feature/interface/zoom validation over all seven tasked root features (zero
    findings) plus ecosystem, plan, reflection distribution, installed-surface, and source-checkout
    contracts.
  - **Outcome**: passed (19 tests).
  - **Evidence**: public workflow promises enforced leaf launches; install/agent/release/one-command
    sources agree on 2.1.0, 17 packaged/18 public/three pairs and plan role transition; planning uses
    exact provider interfaces; reflection triage is action/route conditional, read-only/worktree
    scoped, and nests only public planner identity.
  - **Scope**: public root-level behavior and cross-module consumer promises.
  - **Limitation**: prose guides and templates outside durable feature authorities follow in T033.

- **T033 · FR-005, FR-006, FR-008, FR-013, FR-014**
  - **Check**: stale-count/legacy-plan/literal scan over all nine tasked guides/templates plus seven
    documentation/ontology/projection acceptance-contract modules.
  - **Outcome**: passed (no stale semantic occurrence in tasked paths; 29 tests).
  - **Evidence**: guidance now separates 17 packaged/15 public leaves, two internal planner leaves,
    three Operations/18 public projections; documents public context→author planning, published
    interface-only dependency reads, per-leaf Codex/Claude/outer enforcement, nested standard loop,
    conditional triage, exact installed entry points, and no live-model tests.
  - **Scope**: plan template, README, workflow/skills/ontology/agent/framework/structure/quick-start docs.
  - **Limitation**: exact release-command examples in `docs/releasing.md` are outside T033's authorized
    path list and are handled only if the final T037 task-authorized scan identifies an allowed owner.

- **T034 · SC-005**
  - **Check**: final Archify showcase validate/deliver; docsite declaration validation and atomic
    seven-diagram publication; Concorde diagram/entity/freshness validators; visual-check with a
    one-shot Chrome-for-Testing executable; direct inspection of four light/dark captures; focused
    diagram publication tests.
  - **Outcome**: passed. Changed Operations diagram: 9/9 checks, composition errors 0/warnings 0,
    artifact `sha256:9766032cc1adb74f066cd4090498f8123a7f97c419b25517378d53d441d568b1`
    (712125 bytes), source raw `sha256:ef4201cd4a9bdccb27bf1630c4542bf25c7ecf95f93f439769e14ab00b802bfc`
    (4483 bytes). Atomic publication delivered all seven declared unique outputs with 9/9 and zero
    errors/warnings; docsite validated 45 pages/0 errors; 10 diagram tests passed.
  - **Visual evidence**: containment/readability/viewer chrome passed at 1440×900, 1600×1000,
    1920×1080, and 2048×1320 with no horizontal/vertical overflow; minimum projected text was
    7.356px (required 6px). Inspected 1440×900 and 2048×1320 light/dark captures and contact sheet:
    main/nested/enforcement paths, labels, cards, contrast, spacing, and controls were readable,
    balanced, unclipped, and free of visible overlap. Visual review status: inspected/pass.
  - **Evidence paths**: `generated/architecture/concorde-operations-system-overview.html` and its
    ignored `concorde-operations-system-overview.visual-check.*` sidecars/captures; maintained source
    remains the frozen JSON and disposable outputs are republished by docsite.
  - **Scope**: all changed architecture diagrams (Operations only), complete delivery-set uniqueness,
    freshness, and publication behavior.
  - **Limitation**: `generated/` is intentionally ignored/disposable, so integration checkouts must
    rerun atomic diagram delivery rather than treat HTML/screenshots as source authority.

- **T035 · SC-005**
  - **Check**: `uv run python -m unittest discover -s tests/concorde -t . -p 'test_*.py'`.
  - **Outcome**: passed in an exact temporary integration tree containing this branch plus the
    parent-owned reconciled reflection log; final post-enforcement/evidence rerun passed 370 tests in 19.671s.
  - **Diagnostic history**: the first branch-local run also ran 367 tests and found two failures: a
    stale plan-leaf phase-matrix expectation (updated under T025; focused rerun 2/2 passed) and
    self-validation of R-009/R-019 old concern paths. The parent had already changed only those
    concern locators in main while preserving identity/status/note; substituting that integration
    authority produced the full green run.
  - **Scope**: complete unit, contract, integration, and acceptance Python discovery, including
    policy/process/path, graphs, package/install/update/rollback, release, projections, validation,
    architecture, workspace, reflection, and journey coverage.
  - **Limitation**: this branch intentionally does not commit the parent-owned reflection-log edits;
    final main integration must retain its reconciled log before rerunning the same command.

- **T036 · SC-005**
  - **Check**: canonical Concorde validation locally and in the parent-log integration tree; all seven
    declared Archify showcase validations; agent-surface status; 2.1.0 build/verify plus clean Codex
    install; `npm run check` in `docsite/`.
  - **Outcome**: passed in integrated state. Concorde validation: success, zero findings, source digest
    final post-enforcement/evidence `sha256:bbdd4ba19809281cf37fe4c2f34291b439dbdfc56caaba4262b54163427680b5`.
    Archify: 7×9/9 with zero composition errors/warnings. Agent surfaces: 40/40 current. Release:
    final `concorde-2.1.0.zip=sha256:b509d080157716383b44b426264d5ffc101d9d6d6055b5f3c6dc7e64acc64a58`,
    `release.json=sha256:33e4a2cd4d6d54b1ffb2d3cb0d5185192db657ab10cf85d3ad0cdb6f357eb62d`;
    verifier returned identical digests and installer returned `installed` 2.1.0. Docsite typecheck,
    complete Vitest suite, Profile 7 validation, diagram delivery, and Docusaurus build exited 0;
    Build Manifest 10 has 45 pages/49 routes and all three checks passed.
  - **Branch-local diagnostic**: direct validation has exactly two `CONCORDE-REFLECT-004` findings
    for old R-009/R-019 concern paths; the parent-owned log already reconciles those paths, and that
    byte substitution alone yields the zero-finding result above.
  - **Scope**: deterministic source model, diagrams, projections, package/install/release, and full
    documentation publication.
  - **Limitation**: `npm ci` reported 10 moderate/20 high audit advisories in the existing locked
    docsite dependency tree; no lock update/audit fix was authorized, and the complete docsite check
    still passed. Temporary verification/install/release directories remain under `/tmp` only.

- **T037 · FR-005, FR-006, FR-008, FR-013, FR-014**
  - **Check**: repository-wide semantic scan across maintained package sources, agent assets,
    specifications, guides/templates, and tests for stale 16-leaf/two-Operation counts, canonical old
    plan leaf path, `OPERATION_SKILLS`, leaf-only composition, 2.0.0 release examples,
    Codex `default_permissions`+legacy sandbox mixing, and permissive Claude fallback settings.
  - **Outcome**: passed (`semantic residue scan: clean`) after updating the one stale triage
    leaf-only sentence and task-discovered `docs/releasing.md` 2.1.0 commands.
  - **Negative/owned occurrences**: public `.agents/.claude/skills/concorde-plan` paths are the
    intended stable Operation target; tests retain explicit negative assertions for removed canonical
    `skills/concorde-plan/SKILL.md` and `OPERATION_SKILLS`; Operations architecture names
    `sandbox_mode` only to forbid mixing. Reflection specialist templates still use isolated legacy
    sandbox roles but never contain `default_permissions`, so no profile/sandbox mixing exists.
  - **R-015 audit repair**: Analyze now declares its full prompt-maximum reflection write while every
    triage investigate binding narrows writes to empty. Runtime/static validation fail before executor
    on missing leaf launch factory, null/non-frozen launch spec, missing nested dispatcher, widening,
    or downstream failure; real nested-dispatch tests prove inner context/author get independent
    enforced launches. Focused enforcement/topology/projection suite passed 46 tests; final integrated
    full suite passed 370.
  - **Scope**: maintained semantic residue and final fail-closed enforcement coverage.
  - **Limitation**: specialist reflection-agent sandbox templates remain a separate non-profile
    projection contract; converting that contract was not task-authorized and no mixed config is emitted.
