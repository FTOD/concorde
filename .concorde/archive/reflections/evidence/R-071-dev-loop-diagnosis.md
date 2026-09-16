# R-071: archived read-only diagnosis

Recorded on 2026-09-10, before the subsequently authorized manual integration. Source findings and proposals below are historical diagnostic evidence; they do not claim a completed formal triage, implementation, or delivery. Repository links are relative to this evidence file.

**已证实，dev-loop 的第一个阻塞是恢复实现缺陷：它把“请求带 change_id”误当成“目标已绑定”，在进入路由和开发 graph 之前触发 `KeyError: 'target_id'`。`specify:true` 同样失败。** 前一助手把这个异常归因于“workflow 缺少绑定、`specify:false` 无法进入作者”，因果顺序不成立。

workflow 确实没有 Module 文件绑定，但这是后续正常开发权限需要解决的问题。最终验证使用当前候选 Spec，不是永久固定的原始 Spec。当前 deliver 拒绝缺少 ready 证据，符合现有实现。

以下结论来自只读源码、完整相关 Module Spec、测试和已有工件；没有修改文件、运行 capability、改动生命周期或操作分支/worktree。

**A．实际调用顺序与直接异常**

首次请求的顺序是：

1. `run_capability()` 验证 build、配置和请求，判定 dev-loop 是 mutation。
2. **先调用 `_worktree()`，后调用 `_dispatch()`。** primary 上默认不允许原地开发，于是 host 创建候选。
3. `create_worktree()` 从 committed HEAD 建 worktree；`ensure_change()` 明确初始化 `target_id=None`、`targets={}`、`phase="created"`；源码 checkout 随后构建自身输出。
4. 返回 handoff 后，`run_capability()` 抛出 `worktree_handoff_required`，**尚未进入 main routing，也没有绑定 owner 或启动任务 Agent**。

证据：[调用及 handoff 顺序](../../../src/concorde/development/capability_host.py:2139)、[worktree 分支](../../../src/concorde/development/capability_host.py:146)、[空目标初始化与创建](../../../src/concorde/harness/change_worktree.py:271)。这也符合 [worktree-handoff 场景](../../../specs/concorde/development/module.md:145)。所以，**首次合法地产生未路由的 change，并非异常状态。**

恢复时则是：

```text
_worktree()
  → ensure_change() 返回已有 change
  → _dispatch()
  → 因请求存在 change_id，跳过 MainInvocation.select_one()
  → bind_owner()
  → task["target_id"] 抛 KeyError
```

精确故障点为 [change_worktree.py:320](../../../src/concorde/harness/change_worktree.py:320)。错误前提在 [capability_host.py:2033](../../../src/concorde/development/capability_host.py:2033)，绑定调用在同文件第 2051 行。异常随后被 [通用异常处理](../../../src/concorde/development/capability_host.py:2194) 转为日志中的 `execution_failed`、message=`'target_id'`。

正常路由分支本应先从 entry Module 开始 discovery，校验并选择唯一 route，再填入 `target_id`、绑定 owner、构造 `Invocation`，最后进入 `loop()`。相关入口是 [MainInvocation](../../../src/concorde/development/capability_host.py:253)、[select_one](../../../src/concorde/development/capability_host.py:519) 和 [dispatch](../../../src/concorde/development/capability_host.py:2033)。

我提取了基线和当前源码中的原始 `_dispatch()`、`bind_owner()`，以纯内存替身代替状态读写、路由和 graph 构造，得到：

| 源码 | specify | 结果 | 路由／graph／状态写入 |
|---|---:|---|---|
| `2c398af9…` | false | `KeyError('target_id')` | 均未发生 |
| `2c398af9…` | true | 同上 | 均未发生 |
| 当前代码 | false／true | 同上 | 均未发生 |

这验证了源码路径，与 [JSONL 第 18 行的完整调用和响应](R-071-invocations-and-probe.json) 一致。

已有测试分别覆盖了创建 handoff 和首次无目标路由，却没有连起来验证“handoff 后仅带 change_id 恢复”：[handoff 测试](../../../tests/concorde/harness/test_worktree_lifecycle.py:145)、[首次路由测试](../../../tests/concorde/harness/test_scoped_protocol.py:431)。

**B．路由、开发阶段和最终验证是三件不同的事**

默认完整阶段顺序为：

```text
目标路由与绑定
→ specify
→ Spec review
→ plan 内部的 context-solve
→ plan
→ tasks
→ implement
→ validate
→ code review
→ ready
```

`specify:false` 仅跳过 authoring；reviews 仍默认开启。恢复时可以复用当前 plan/tasks/implementation，但仍检查所需 review。源码依据：[graph 构造与恢复裁剪](../../../src/concorde/development/capability_host.py:1755)、[plan 的前置检查](../../../src/concorde/development/capability_host.py:1275)。

**候选 Spec 的刷新机制已经存在：**

- author 返回文档替换，由 host 验证、应用，再重建 repository：[author](../../../src/concorde/development/capability_host.py:1188)。
- 每个 graph 节点重建 repository，子阶段创建新的 `Invocation` 和 snapshot：[节点执行](../../../src/concorde/development/capability_host.py:1880)。
- validation 从候选目录重新读取 Spec；实际上结构验证遍历整个 registry，而非拿初始 discovery snapshot 验证：[validate](../../../src/concorde/development/capability_host.py:1631)、[validator](../../../src/concorde/spec/validation.py:518)。
- ready 再检查 review、未解决 gap、任务完成、Spec/code/check digest 和候选树：[verify_completion](../../../src/concorde/development/capability_host.py:1685)。
- review 的 `base_commit` 用于生成差异；**当前完整 Spec 才是审查合同**：[review.inputs](../../../src/concorde/development/review.py:71)。

因此，独立 `main action:ask` 的 `spec_incomplete` 既不是原 dev-loop 内部路由结果，也不是最终验证结果。它不能证明 dev-loop 曾执行到 Spec author 或 validation。

还有一个容易遗漏的现有路径：没有 authored targets 的维护候选可以运行正式 `validate`，执行全项目配置检查并记录 direct-candidate evidence；这已在 [接口 Spec](../../../specs/concorde/development/interfaces.md:371) 和 [实现](../../../src/concorde/development/capability_host.py:1636) 中定义。**外部测试日志不会自动进入这条证据链。**

当前 primary inventory 仍记录目标为空、`deliver/blocked/incomplete_change`：[元数据](R-071-maintenance-integration.json)。deliver 在 [第 240 行](../../../src/concorde/harness/worktree_delivery.py:240) 要求 ready 状态及 `validated_tree`，在检查真正集成之前就会拒绝。`merge-tree` 无冲突不能满足这个条件。

**C．文件绑定与拓扑路径的真实情况**

我对原基线、修复提交 `22251f49…`、当前工作区分别检查了全部七个 Module 的 registry 和文档内 entity 声明；三者结果相同，实体声明并集均与 registry 一致：

| 文件 | 声明绑定 |
|---|---|
| `.github/workflows/validate-source-checkout.yml` | 无 |
| `tests/concorde/harness/test_studio_server.py` | `module.harness` |

权威库存是 [.concorde/specs.json](../../../.concorde/specs.json:1)。这证实了 workflow 的**实现绑定缺口**，但不等于“职责无法路由”，也不等于必须找到排他的唯一文件 owner：协议允许多个 Module 共同绑定同一实现，随后分别验证。

未绑定也不必然造成最终结构验证失败。Spec 将 unlisted file 定义为 warning；当前扫描甚至只遍历已有绑定涉及的顶层目录，未必发现 `.github` 下的遗漏：[结构验证合同](../../../specs/concorde/spec/structure.md:96)、[扫描实现](../../../src/concorde/spec/validation.py:331)。

隐藏路径需要区分规则与实现：

- canonical [P5](../../../generated/protocol/principles.md:844) 的文字排除点前缀目录和文件。
- 实现中的排除主要发生在目录递归展开；**精确文件绑定不经过该过滤，显式目录本身也不检查点前缀**：[expand_entry](../../../src/concorde/spec/repository.py:132)。
- 内存复现确认，基线与当前 resolver 都会展开显式 `.github/workflows/validate-source-checkout.yml`，也会展开显式 `.github/workflows/`。
- writer 的 authority roots 来自 declared entries；没有针对 `.github` 的额外统一禁止：[implementation_paths](../../../src/concorde/spec/repository.py:611)、[权限构造](../../../src/concorde/development/capability_host.py:1098)。

所以，**不能声称“显式绑定仍一定不可写”；这里存在需要澄清的协议／实现边界不一致。**

现有拓扑能力并不缺失：

```text
main design-topology
→ 接受设计
→ accept-topology：各 Module 独立 author，验证 overlay
→ 接受具体 application
→ apply-topology：原子应用 registry 与文档
```

当前没有名为 `create/refine` 的 main action；有效 action 见 [main.py:14](../../../capabilities/main.py:14)。上述流程能处理新增 Module，也能处理已有 Module 的 file-binding 变更：[绑定变更任务检查](../../../src/concorde/development/capability_host.py:634)、[author 与 overlay](../../../src/concorde/development/capability_host.py:811)。

普通 specify 则只能修改已有注册文档，不能增删 file listing；否则 registry/entity union 校验失败。其明确限制见 [specify 模式源文件](../../../agents/spec_engineer/modes/specify.md:8)、[host 校验](../../../src/concorde/development/capability_host.py:1238)。

连接处还存在实际限制：[`_apply_topology()`](../../../src/concorde/development/capability_host.py:958) 使用候选 registry 的 **entry_target** 作为 change owner。已有单目标 change 若 owner/task 不匹配会被拒绝；未绑定 change 则会被绑定到 entry Module。因此不能只给 dev-loop 加一条调用 main 的边就完成衔接。

**D．建议的最小修改范围**

以下是实现建议，不是本次执行结果。

1. **先独立修复未路由 change 的恢复。**
   在 `_dispatch()` 前建立明确的恢复准入：验证 change 所属 worktree；根据持久化 owner 和可信 `host.routed_target` 区分“未绑定”“已绑定”“内部子调用”。未绑定时必须重新 routing，即使请求含 change_id；已绑定时从记录恢复目标并校验 task/focus/constraints。调用者提供的 target hint 不能替代路由证据。`bind_owner()` 对缺少必要字段返回结构化错误，不能泄漏 KeyError。保留已有 handoff，不需要搬动创建顺序来修复。

2. **将缺口分型，并给出可恢复的下一步。**
   建议结果区分：`missing_contract`、`unbound_file`、`unknown_target`、`excluded_path`、`conflicting`、执行失败。保留现有 gap provenance，同时提供阻塞阶段、所需路径／合同、下一动作及恢复身份。未知 owner 不应伪装成已选目标；当前 stage response 强制非空 target 的形状也需要处理：[response schema](../../../src/concorde/spec/contract_shapes.py:60)。路径仅是定位信息，不能授予读取内容或写入权限。

3. **增加受控的 Spec／topology 修复返回边。**
   当前合同明确规定唯一自动修订边是 `review_code → tasks`，其他失败停止：[Development requirements](../../../specs/concorde/development/module.md:69)、[实际 stop](../../../src/concorde/development/capability_host.py:1825)。因此新增能力要同步修改合同，而不能称为“修复一条现成自动边”。最小方案是保存暂停点：
   - 本地缺失合同 → 明确授权的 Spec repair → 新 Spec review／assessment → 重建受影响 plan。
   - binding／membership／新 Module → 现有 topology proposal/application 流程 → 重新路由／绑定 → 恢复开发。

   topology 子流程必须保留原 development intent 与 owner，不能沿用当前 apply 对 owner 的无条件重设；修改 owner 时需要显式、可核验的重绑定记录。

4. **明确 `specify:false` 的停止语义。**
   一旦确认必须改 Spec，应返回“需要 Spec／topology 变更”及准确恢复动作，保存候选并等待明确的策略变更，不能偷偷切为 authoring。反过来，`specify:true` 也不能允许普通 author 修改 registry。恢复还要处理已有 `authored_specs` 会跳过 author 的条件：[第 1781 行](../../../src/concorde/development/capability_host.py:1781)；仅把 flag 改成 true 不保证重跑所需作者。

5. **复用现有 freshness 机制，补齐拓扑修复后的失效传播。**
   应用新 Spec／registry 后同时重建 repository、重新选择 target descriptor、生成新 snapshot；失效受影响的 plan/tasks、review/check、consumer evidence 和 `validated_tree`，保留历史。原节点目前只重建 repository；加入 topology 后不能继续使用缓存的旧 `self.target`。gap 应由对应新 assessment 成功后关闭，不能因为“文件改了”全部清空。ready 和 delivery 校验继续保留。

6. **统一隐藏路径合同。**
   建议明确“目录遍历的默认排除”和“显式声明的普通项目文件”的区别，使 `.github/workflows/...` 可被明确建模；项目控制路径、生成输出和凭据拒绝规则仍需独立保留。源码修改位置包括 [Framework profile](../../../prompts/protocol/framework-profile.md:15)、resolver、权限与反向索引，不能只改一句提示或直接编辑 generated。

必要回归测试至少包括：

| 测试组 | 必须验证的行为 |
|---|---|
| handoff→resume | 无 target 创建后仅带 change_id 恢复；specify 两种值、reviews 两种值；恰好一次有效路由 |
| 恢复准入 | 已绑定恢复、错误 change/worktree、冲突 hint、变更 intent、可信内部子调用 |
| 缺口恢复 | 未绑定文件、新文件位于已绑定目录、缺失合同、排除路径分别返回正确类型；false 不启动作者 |
| topology 衔接 | binding-only 变更、保留原 intent/owner、两个接受点、stale artifact、拒绝与回滚 |
| freshness | 作者更新的字节进入后续 review/plan/validate；旧 descriptor、plan、review/check 均不能通过 ready |
| 文件边界 | 精确隐藏文件、显式隐藏目录、普通目录下隐藏后代、控制路径、共享实现用户一致性 |

可以扩展现有 [review 顺序与 freshness 测试](../../../tests/concorde/development/test_review.py:285)、[Spec repair 恢复测试](../../../tests/concorde/development/test_review.py:329)、[目录绑定测试](../../../tests/concorde/spec/test_module_model.py:187)，不必重写整套机制。

**E．独立 review 的失败，以及证据限制**

两份 [首次结果](R-071-invocations-and-probe.json)、[重试结果](R-071-invocations-and-probe.json) 均对应 [discover_routes 第 502–505 行](../../../src/concorde/development/capability_host.py:502)：模型返回的 task 或 constraints 与输入不完全一致，因此 reviewer 尚未启动。

**现有证据不足以将它认定为另一处 Python 实现 bug。** 精确保留 intent 是现有合同和[测试明确要求](../../../tests/concorde/harness/test_scoped_protocol.py:446)，目前没有两次原始 route payload 可比较具体差异。可改进的是让模型只返回目标选择，由 host 保留原 task/constraints，并记录字段级失败诊断；不能简单删除校验或接受模型改写。

对前一助手的判断应作三项纠正：把独立 ask 当成 dev-loop 已执行的内部阶段，是操作解释错误；把 `specify:false` 当成 KeyError 原因，是实现判断错误；把“补候选 Spec 后验证”当作唯一且已证明可行的恢复路径，遗漏了 topology owner 限制和现有 direct-candidate 验证合同。

本次基线固定为 `2c398af9…`。诊断开始时 primary 为 `ce15a3d3…` 且有用户修改；期间外部会话提交为 `1af181b1…`。`typed_data.py` 的 native-only 配置变更属于后者，不能回溯为原故障原因；本报告涉及的关键 host、worktree、review、resolver 和 Framework profile 已核对与原基线字节一致。

未读取其他 worktree 的源码或本地状态文件，未重跑长测试或正式 review。首次 handoff 依据用户事件、primary 元数据及源码核实；650/27/86 项验证仅作为[既有维护报告](R-071-prior-ci-verification.md)中的证据，**不构成本次新验证，也不解除原 lifecycle 阻塞。**
