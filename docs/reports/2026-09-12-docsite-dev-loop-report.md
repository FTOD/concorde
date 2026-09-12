# Docsite graph view 移除：dev-loop 问题与修改报告

报告日期：2026-09-12。本文回顾本次任务从启动、维护、恢复、审查到交付的实际过程，重点说明为什么 dev-loop 多次停住、做了哪些修改，以及哪些问题来自我的执行判断。本文是事后执行报告，不是 Reflection，不创建队列记录或改变任何问题的处置状态。

## 1. 结果与报告范围

代码已经正式交付并合并到本地 `main`：

| 项目 | 实际结果 |
| --- | --- |
| 最终代码提交 | `0063338297944848218a695c10d1b8ac69d44db0` |
| 最终代码树 | `582d98137c043278dcc5f03784ea43b0a69fb9c0` |
| 合并前 main | `9b001d9190cadad1f487d317df564441547dfe21` |
| Change | `change.5168b485-c195-417f-8ecb-5861cd9183f9` |
| 交付分支 | `concorde/delivered/change.5168b485-c195-417f-8ecb-5861cd9183f9` |
| 交付与合并 | 回执分别记录 `delivered`、`primary_merge.status = merged` |
| 工作树清理 | 源工作树已删除，`cleanup_error = null` |
| 验证 | 最终 dev-loop 六项检查通过；交付及 main 合并各自七项检查通过 |
| 审查 | 必需审查和补充的独立 Harness 审查均无 blocking、无 Spec gap；保留 advisory |
| 生成文件 | 合并后重新 build，`build --check` 返回 `differences: []` |

原始任务是删除 docsite 的独立 graph view，保留其他阅读、导航及 UA 图能力。后来你明确授权 delivery 和 main 合并，并补充了当前文档链接应保持有效的要求。报告将这几个阶段都纳入，但不把后续新增要求说成最初就已经确定的范围。

最初的功能删除提交 `5b1c4cfb` 在 2026-09-11 09:25 UTC 已完成；正式 main 合并与本地生成文件同步直到 2026-09-12 才完成。因此，耗时主要不能用“删除图页面很复杂”解释：大量工作来自运行时、流程恢复、合同与实现不一致，以及我在范围控制和交付预检上的返工。

本文以 Git 提交、实际 Host 结果、测试日志和交付回执为依据。上述代码快照不包含随后生成的本报告。合并完成并重建时工作区干净；报告文件属于之后新增的文档。

## 2. 问题总览

| 问题 | 直接后果 | 最终处理 |
| --- | --- | --- |
| 原生 Codex 精确文件写权限与元数据遮罩不兼容 | worker 在执行前遇到 `ENOTDIR` | 对真实普通文件做受限适配，保留目录和别名拒绝，启动前复核 |
| worker 的 Node 与 Host 选中的 Node 不一致 | 外层可运行的前端命令在 worker 中失败 | 认证既有 Node 文件、只读授权并固定 shell PATH |
| implementation 被要求完成后续 Host 才能执行的检查 | 代码已实现，但任务无法完成；形成阶段先后循环 | 明确 worker 局部验证与 Host 仓库验证职责，增加受摘要约束的任务恢复 |
| 任务作者看不到历史任务 ID | fresh author 反复生成已被保留历史占用的 ID | 增加 typed identity constraints，保留身份唯一性检查 |
| 完整 Module 上下文被误当成必须修复全部功能的任务范围 | 独立 UA、viewer、scaffold 等问题不断进入任务 | 收紧审查、规划和任务指引；独立问题保留 advisory，不强制改判 |
| review gap 的失效规则不完整或身份不稳定 | 修正审查输入后仍无法重评，或生命周期变化误触发重评 | 使用稳定 review input digest，保留失败和不完整审查的旧 gap |
| 已协调任务不能安全重绑 | scope repair 改了父任务，但子组件保留旧 intent，恢复失败 | 保留路由和历史，重绑变化组件，重新生成其后续证据 |
| task-control 准入缺少阶段或条件检查 | 非 tasks 阶段可接收控制值；反馈可缺少原任务列表 | 补阶段门和完整 launch 输入的条件依赖 |
| 已解决的组件 gap 仍留在父缓存 | 正确修复并重新审查后，scope repair 仍被拒绝 | 按目标、任务、上下文和 gap 内容匹配真实解决记录，并支持嵌套组件 |
| 文档链接保证与历史别名语义不清 | Spec review 多次阻止继续 | 按你的明确意见规定当前发布文档内链有效性，不引入历史别名存储 |
| 新链接校验器对 query、redirect base、编码路径处理不完整 | 有效链接误拒绝，或失效内链被误判为外部链接而漏检 | 增加最终 HTML 校验和逐项真实回归 |
| 检查依赖已有 `node_modules` | 常驻候选可过，冷交付检查目录无法运行 | 从实际检查目录复制源文件，在 scratch 按 lockfile 安装依赖 |
| main 与候选分别维护后出现合并冲突 | 第一次正式 delivery 被拒绝 | 保存候选提交，合入 main、逐块保留双方修改，再完整验证 |

## 3. 启动和运行环境问题

### 3.1 精确文件写权限触发原生沙箱错误

Concorde 的 implementation 权限可以只授权一个具体文件，而不授权整个父目录。此次遇到的 Codex 原生行为会在可写根下处理 `.git`、`.codex`、`.agents` 元数据路径；当可写根是普通文件时，这些目录式操作会触发 `ENOTDIR`，worker 尚未执行任务就失败。

修改位于 [permissions.py](../../src/concorde/harness/permissions.py) 和 [agent_executor.py](../../src/concorde/harness/agent_executor.py)：

- 仅对已经存在、不是 symlink、没有额外 hardlink 的普通文件进行适配。
- 在该文件下面声明不可达的元数据子路径，避免目录遮罩冲突；这些路径仍受普通文件边界约束。
- 不把父目录变成可写，不对目录套用这种适配，也不覆盖已有 deny。
- 启动前重新检查原始授权输入，文件类型或别名关系变化会使准入失败。

这属于 Concorde 对运行时行为的兼容修复，不是关闭 sandbox。对应提交是 main 的 `1c5773df` 和候选的 `e69938a8`。

### 3.2 外层 Node 可用不代表 worker 使用同一个 Node

外层使用的 Node 为 `v22.23.2`，但 worker 受到文件可见范围、shell 初始化和 PATH 的共同影响，不能仅凭外层 `node --version` 就证明它能运行项目工具链。早期前端命令失败与 Node 环境不一致有关，例如所需的 `styleText` 能力。

在 [agent_executor.py](../../src/concorde/harness/agent_executor.py) 增加 Host 选择既有 Node 的认证，在 [permissions.py](../../src/concorde/harness/permissions.py) 绑定实际启动配置：

- Node 由 Host PATH 选择，任务输入不能指定任意工具作为例外。
- 绑定文件路径、内容摘要、大小、权限和所有者等证据；检查 hardlink 和祖先目录可信性。
- 只授予该 Node 文件的只读访问，不把安装目录及相邻文件一并开放。
- 固定 worker shell PATH，并关闭会覆盖工具链选择的 login/profile/snapshot 行为。
- 执行前重新选择和认证，防止预检后 Node 被替换。
- Spec capsule 不增加 Node 特例；适用范围是原生 Codex 的 implementation-workspace。

`f2c5f7e2` / `80088c3c` 是这组主要修改。真实原生沙箱测试验证了 Node 版本、子进程 PATH、运行时只读以及相邻路径访问拒绝。

### 3.3 检查命名空间暴露了测试夹具问题

之后又出现一次表面上类似的 Node 认证失败，但原因不同：在 Host 检查的 user namespace 内，某些 Host root 所有的祖先目录被映射成 UID `65534`，而测试仍假定它们表现为 UID `0`。

我保留了生产认证规则，修改的是测试夹具：投影测试使用专门的 Node 文件和明确的 resolver 替身，仍执行真实文件认证和启动前重验；真实 Node 执行另由原生沙箱测试覆盖。这样不会把“测试配置投影”冒充“真实 Node 执行”，也不需要放宽祖先目录信任或跳过测试。

对应候选 `15626fc8`、main `f65a93d7`。当时真实 `execute_check` 运行 125 项 runtime 回归，零失败、零错误、零跳过。

## 4. dev-loop 的任务、验证和恢复问题

### 4.1 implementation 的验收条件要求了尚未发生的 Host 行为

普通 implementation worker 只获得当前 Module 授权的实现文件。完整仓库测试会导入 `tests.concorde.support`、其他包和配置，这些文件可能不在 worker 的 grant 中。早期任务却把“完整仓库检查结束”写成 worker 完成任务的前提，而 Host 又要等 implementation 完成才运行检查。

这形成了实际的顺序矛盾：worker 为了完成任务必须先做它无权执行、且由后续阶段负责的动作。

最终修改有两部分：

1. 在 [implementation 指引](../../agents/programmer/modes/implementation.md) 及 Development/Harness 合同中区分局部验证和 Host 仓库验证。worker 执行授权范围内适用的检查；缺少仓库级输入时记录具体命令和缺失输入，不能把没有执行的测试报成通过。真实实现义务未完成时仍不能标记完成。
2. 配置 `check.views.repository-regressions`，通过 Host 的只读检查机制独立取得所需仓库输入。实现任务完成不代表 ready：Host 检查失败仍会阻止代码审查或最终就绪。

主要提交为候选 `c32abbca` 和 main `4c451a0e`。main 当时还增加了“implementation 已完成但 Host 检查失败，仍不能 ready”的控制流回归；最终修复了该测试不准确的场景声明，见第 7 节。

### 4.2 用有约束的恢复入口替代手改任务状态

已经保存的错误验收任务不能靠改提示词就自动消失，也不能直接改 `.concorde` 状态把它们设成完成。因此增加了 `repair_task_scope:{tasks_digest}`：

- 请求必须绑定当前未完成任务列表的规范化摘要。
- Host 将原 plan、原任务、身份保留集合和固定的 `implementation_boundary` 反馈交给新的任务作者。
- 新任务从 incomplete 开始；原任务和相关修订保留在历史中。
- 过期摘要、未解决 gap、不合法替代、已完成列表等仍受拒绝规则约束。
- 恢复后必须依次经过 implementation、validation 和所需 review。
- 已消费请求的重放恢复当前进度，不重复改写历史，也不能抢占正常的 code-review repair 边。

入口与控制流见 [capability_host.py](../../src/concorde/development/capability_host.py)、[Development 恢复约定](../../specs/concorde/development/development.md) 和 [dev-loop 请求说明](../../prompts/workflow-host/dev-loop-flags.md)。这是一条显式恢复入口，不是遇到任何失败都自动重试的新循环。

### 4.3 任务 ID 保留规则存在，但作者看不到保留集合

fresh task author 不知道历史中已经使用过哪些 ID，容易生成形状正确、内容合理、但身份冲突的任务。Host 拒绝是正确的，缺失的是输入。

`a8a0ab0b` / `afeb5043` 增加 `concorde-task-identity-constraints@1`，向 tasks 阶段提供 `reserved_task_ids`。集合包含相关历史任务及待替换任务的 ID。它只限制身份，不增加功能义务、实现内容或权限。重复 ID 会明确报错，不由 Host 悄悄重命名或覆盖历史。

### 4.4 搜索指令也需要遵守冻结文件清单

worker 曾使用过宽的搜索范围，搜索到了未授权路径。修正 [implementation 指引](../../agents/programmer/modes/implementation.md)，要求从冻结的 `implementation_files` 出发，对明确路径或允许目录搜索；目录可写声明不意味着可以读取任意同级内容。

对应 `2de47801` / `c0c13560`。这是工作方式的指引修正，文件权限仍由既有执行机制强制执行。

## 5. 审查范围、规划范围和证据身份问题

### 5.1 完整上下文不等于本轮修复范围

每个审查者应阅读完整的 Module Spec，但这不等于删除 graph view 时必须一并修复该 Module 的全部既有功能。早期审查会把独立 UA 的边界问题作为当前任务的阻塞，规划和任务作者也会把“保留现有功能”展开成全面重做 viewer、scaffold、Mermaid 和其他能力。

修正 [共享审查指引](../../prompts/workflow-host/review-scope-and-result.md)、[Spec review 指引](../../agents/spec_engineer/modes/spec-review.md)，要求说明 blocking 与任务、依赖、兼容性或受影响消费者之间的具体因果关系。完整上下文继续保留；真实独立问题仍记录为 advisory；既有问题如果确实阻止当前任务，也仍可 blocking。

之后还在 [plan](../../agents/spec_engineer/modes/plan.md)、[tasks](../../agents/spec_engineer/modes/tasks.md) 和 implementation 指引中统一说明：保留能力不是自动新增全面整改任务；验收应围绕请求的行为变化和必要保留证据。

这里没有加入 Host 强制降级严重度的过滤器。实际新审查曾在将独立 UA 问题列为 advisory 的同时，继续拦截真正的导航回归、链接缺陷和任务恢复错误。这些结果说明“范围修正”并未强制审查通过。

主要提交为 `74bd2564` / `77db1e6f`；后来的 plan/tasks/implementation 三组指引及 golden 修改收录在 `fb2a7641`。

### 5.2 改了审查输入，却无法重新审查旧 gap

早期持久化 gap 主要按 Spec digest 决定是否允许重评。即使修正了 reviewer 指令，Spec 字节没有变化，正常流程仍会被旧 gap 短路。

修改 [review.py](../../src/concorde/development/review.py)、[change_worktree.py](../../src/concorde/harness/change_worktree.py) 和 capability Host，记录并比较稳定的 review input digest：

- 真实相关输入变化后可以进行新审查。
- 生命周期状态自身变化不能被当成问题已修复的证据。
- 只有完整、被接受、无 blocking 和 gap 的重评才解除对应阶段的旧 gap。
- 失败、不完整、仍有阻塞的结果保留旧 gap；旧格式记录仍遵守原有约束。
- 无关任务或阶段的成功不能擦除其他归属的缺口。

后续 `90fbdf92` / `87c8c0b6` 又修正了协调恢复和稳定身份的细节。没有通过改缓存、删 gap 或重写审查结果制造 ready。

## 6. 协调任务和缺口归属的真实缺陷

### 6.1 父任务修好了，子组件仍绑定旧任务

coordinated task 的验收文字变化会改变派生的 component intent。原恢复机制未完整处理这些绑定，导致父任务接受了替代列表，但子组件仍按旧任务工作或触发 stale-context。

修改后的恢复保持组件 target set，不允许借恢复改变路由；保存旧 coordination 记录；只清除变化组件的 implementation 完成状态和 enclosing finalization stamps，保留未变参与者及仍有效的 Spec 对齐状态。子组件用新 intent 正常进行必要的 review、plan、tasks、implementation 和 validation。

这组修改在 `90fbdf92` / `87c8c0b6` 中落地，有受支持公开流程的 fixture 回归，而不是仅测试内部字典赋值。

### 6.2 直接子组件的缺口已解决，父缓存仍阻塞

组件重新完成 Spec 修复和审查后，durable gap history 已更新，但父 coordination 缓存仍保留原 gap。原判断只看缓存非空，会永远拒绝恢复。

`efcd5921` 增加归属匹配：只有目标、任务、gap 内容及原观察上下文相符的 resolved history，才能释放对应缓存；open、缺记录、错误归属和错误 context 仍拒绝。

### 6.3 上述修复还漏了嵌套组件

后续独立审查指出：在 `bank → audit → transfer` 这种链中，bank 的 audit 缓存可能携带真正属于 transfer 的 gap。只按直接子组件 audit 的 target/task 过滤 history，会在比较前就排除正确的 transfer 解决记录。

最终 `00633382` 在 [capability_host.py](../../src/concorde/development/capability_host.py) 中沿已有 coordination 记录收集可归属的 `(target, intent)`；仅在组件自身任务与记录一致时继续向下遍历。随后仍匹配实际 gap owner、完整 gap 字段和观察 context，并保留 open history 阻塞。

[新增三层回归](../../tests/concorde/development/test_review.py) 真实执行了 gap 产生、Spec 修改、成功重评和父 scope repair。修复前失败，修复后成功；九类错误记录或链状态，包括 wrong target、wrong task、wrong context、reopened、missing coordination 等，仍拒绝并保留已接受的 tasks/history/coordination。

这是第二次审查发现第一版修复不完整的实例，不能把早期独立审查通过当作永远覆盖后续版本的证明。

## 7. Typed 输入和测试声明问题

两个新增 task-control 值最初还缺少各自所属 Module 的完整本地语义。后续补齐了字段、版本、错误、无副作用、阶段用途和输入边界，不能仅依赖实现源码让普通 Spec worker“猜出合同”。相关提交包括 `c4b9f41d` / `355ca24d`、`9b001d91` / `ac75849e`。

随后修正了三类具体缺陷：

1. **tasks-only 检查不能只依赖选择了 mode。** `efcd5921` 在 context 准入中补充独立的阶段检查，防止 `mode=None` 时在其他阶段接受 task-control 值。
2. **带 scope feedback 时必须有 prior tasks。** 原 `validate_mode_artifacts` 只检查 allowed types 和无条件 prerequisites，完整 launch 可接受 plan + identity constraints + feedback，却没有 implementation-task。`00633382` 增加条件依赖，保留普通首轮 tasks 和 partial policy preview 的构造行为。测试同时覆盖 launch 构造、executor preflight 和执行前拒绝，并断言无 model runner/probe 调用。
3. **测试的 `verifies` 声明必须与实际触发和结果一致。** `e53a9037` 加强 task-control 错误 code/field 及重复验证无项目 I/O、无生命周期副作用的断言。最终又把“Host 检查故意失败”的回归改为声明 `scenario.development.validate-blocked`，不再声称验证成功 ready 或从未提交请求的 task-scope repair。

最后一组四文件修复有两项真实 red → green 回归和 127 项相关测试通过。测试替身用于控制模型输出和检查流程；不把它们说成真实模型质量或全平台安全性的证明。

## 8. Docsite 实际修改和链接保证

### 8.1 删除了什么，保留了什么

删除独立 `graph.tsx` 页面、`ScopedGraph.tsx` 组件、Graph 导航入口、独立图投影/构建产物及直接 Cytoscape 专用依赖，更新相应测试和英文 Spec。发布 schema 随图产物移除从 17 更新到 18。

保留注册文档阅读、目录和 Module 导航、稳定 ID anchors、来源信息、inline Mermaid、可选 reading collections、instruction/wire projections，以及独立 UA exporter/viewer。UA 关系信息与 Module 依赖验证没有随着 docsite 图页面一起删除。

阅读导航调整曾误去掉 Module category 的直接文档链接；后续恢复了原有 category/leaf 语义，目录树以 canonical route 链接到相同文档，避免重复 doc ID。实现见 [materialize.ts](../../docsite/plugins/scoped-content/materialize.ts)，主要修正提交 `adfb6a08`。

viewer 不是完全零修改：最终保留了“遇到首个已存在但无效的图路径应拒绝”的修正及对应验证，避免跳过一个已存在目录再使用后备图。更广的 viewer/scaffold 重构没有保留。

### 8.2 历史别名争议如何收敛

原旧链接承诺涉及成员关系变化，但缺少历史别名输入和保留策略。处理过程中先后出现过缩窄旧承诺、额外实现历史别名机制、仅写明未决问题等尝试；这些不能替代用户对行为的决定。

你后来明确指出：只要 A 当前文档仍链接到该文档，就应保证该链接有用；归属完全改变时，A 不一定还应保留那个链接。最终 `2e24100a` 将承诺落到当前发布文档内链有效性，当前 membership 仍用于派生别名，不新增独立历史别名库。

具体说：文档转到 B 后，A 当前文档如果仍以有效源路径或 canonical route 引用它，引用必须能解析；如果 A 保留了已经无法解析的旧别名，发布应失败并指出链接，而不是静默接受，也不是悄悄新增历史存储。

### 8.3 最终 HTML 校验，而不是只检查源 Markdown

新增 [internal-links.ts](../../docsite/plugins/scoped-content/internal-links.ts)，使用直接声明的 `parse5` 解析完成渲染的 HTML。检查 `a/area` 导航、ID 和旧式 named anchors、base URL、redirect，以及 required routes。缺页面、缺锚点或无法解析的内部重定向会报告 referrer 和 destination，并在发布替换前拒绝候选。

回归覆盖了真实 MDX 渲染、文档从 A-only 到 B-only 的 membership 变化、别名 query/fragment 保留，以及失败后上一版构建文件清单和字节保持不变。这里的保证是当前发布站点范围内的静态内部导航；不会联网验证外部站点，也不声称执行任意应用 JavaScript 后的所有动态导航。

### 8.4 校验器自身发现并修复的边界

| 输入或场景 | 原问题 | 修复 |
| --- | --- | --- |
| `other.md?mode=1#entity.x` | 把 query 当作源文件路径的一部分 | 先分离首个 fragment，再分离路径前的首个 query；只用路径查找，保留完整后缀 |
| `?mode=1#entity.x` | 自身文档 query 链接未明确定义 | 明确按当前源文档处理 |
| incoming link → redirect，redirect 含 `<base>` | 沿重定向解析时忽略目标文档的有效 base | 入站遍历与该文档自身导航采用相同 base 语义 |
| Unicode base URL 与编码后的 pathname | 字符串形式不同，被误判为站点范围外 | 按 URL pathname 一致处理 |
| `%E6…` 与 `%e6…` | 百分号十六进制大小写不同导致漏检 | 统一 escape hex case |
| `/docs/` 与 `/%64ocs/` | 等价路径未归一化，缺页或缺 anchor 被跳过 | 解码 ASCII unreserved，保留字面路径大小写及保留分隔符语义 |
| 归一化后截取路径 | 用归一化 base 长度切原始字符串可能错位 | 比较和截取使用同一归一化 pathname |

对应回归既有成功用例，也有缺页、缺 anchor、外部 origin、base 目录边界、保留分隔符及不重复解码 `%` 的拒绝/保留用例。这些链接增量集中随 `fb2a7641` 保存，而不是每一项都有独立 Git commit。

## 9. 冷检查环境与交付冲突

### 9.1 常驻候选能测试，不代表交付临时目录能测试

交付检查使用干净的临时 checkout，没有候选中被忽略的 `node_modules`。早期仓库 wrapper 依赖已有安装：在常驻工作树可过，在冷目录中不能可靠执行。

最终 [run-checks.py](../../docsite/tests/repository/run-checks.py) 先复制实际被检查的 ROOT，并排除已有依赖、缓存和 build，再在独立 scratch/docsite 中运行：

```text
npm ci --ignore-scripts --no-audit --no-fund
```

随后从复制的源码运行 build、Python 回归和 Vitest。安装失败立即退出；依赖准备和生成输出留在 scratch，不复用源工作树或 primary 的安装。`skills-lock.json` 同时进入 Host 检查输入和复制清单。

[wrapper 回归](../../tests/concorde/views/test_repository_checks.py) 覆盖没有依赖、旧安装、实际 package/lockfile 一致性、源文件保全及安装失败不再执行后续命令；还通过真实只读 `execute_check` 验证无 `node_modules` 的普通副本。

### 9.2 第一次正式 delivery 确实失败了

`e6853c28-cbdb-4023-a7d7-0e7f23a3fd30` 返回 `merge_conflict`，没有交付回执、没有删除源工作树、没有推进 main。原因是 main 和候选之前分别承载过通用修复，随后又分别演进；最后集成时产生重叠修改。

处理顺序是：

1. 将已经验证的 19 个候选文件精确保存为 `fb2a7641`，排除原有 AGENTS/CLAUDE 本地修改。
2. 将确切的 main `9b001d91` 合入同一候选分支，实际处理 9 处冲突。
3. 保留候选修复，同时保留 main 的 `skills-lock.json` 支持、deferred Host 检查回归和已有 R-073/R-074 记录。
4. 合并结果 `cf52368b` 相对候选 checkpoint 仅增加 6 个文件的必要差异；再次运行检查和审查。
5. 后来的 `00633382` 修复仍保留 main 祖先关系；只读 merge-tree 复核无冲突后才再次正式交付。

R-073/R-074 是并行工作已写入 main 的既有记录，不是本报告新建，也不应记成这次事后报告的产物。

## 10. 我在执行过程中走偏或做得不够好的地方

这些问题不应全部归因于框架。

| 我的处理问题 | 造成的影响 | 实际纠正 |
| --- | --- | --- |
| 新补的 publication Spec 曾虚构保留接口格式 | 后续 worker 可能为满足新 Spec 改造不该变化的接口 | `1959577d` 恢复 `scoped-materialization.json` schema 1、原 agents/skills 结构和 type-ID→schema wire 映射 |
| 旧链接问题的处理曾引入未获明确语义决策的历史别名机制 | 给删除任务增加了独立兼容性功能 | `4c978363` 撤回额外机制；后来取得你的明确链接要求后再修改合同与实现 |
| “保留功能”被多轮任务扩大成 viewer、UA、scaffold、Mermaid 全面整改 | 出现范围外编辑和大量不必要验收任务 | 保存差异、停止相关 worker，只恢复明确未授权增量；补 plan/tasks/implementation 范围指引 |
| 仅修任务阶段边界，未同时确认 plan 的范围 | 新 tasks 仍继承过大的 plan | 后续通过正常公开 dev-loop 在真正 Spec 变更后重规划，writer 前审计实际任务 |
| 曾尝试直接公开调用内部 `concorde-plan` | 返回 `unknown_capability`，没有生成计划 | 确认 plan/tasks 仅为 Host composition 内部阶段；停止重试，未新增入口或旁路调用 |
| 曾准备改 planner cache 以强制重规划 | 可能扩大 Framework 修改范围 | 撤回该方案；query Spec 的真实修订已足以让公开流程重新规划 |
| 监控一度依赖旧 `phase=active` 状态 | 已停止的进程被误报为仍运行 | 改为核对真实 PID、子进程、退出码及事件；更正旧状态报告 |
| 正式合并冲突检查做得偏晚 | 已跑完一轮 readiness 和独立审查后才被 delivery 拒绝 | 在候选先合入当前 main；之后每次最终提交均先核对 merge-tree |
| 初次 gap 缓存修复只覆盖直接子组件 | 后续独立审查又发现嵌套恢复缺陷 | 增加真实三层流程及错归属拒绝回归，最终四文件修复通过重新审查 |
| 测试声明曾比测试实际覆盖范围更宽 | 覆盖报告看起来比真实验证更完整 | 更正 failed-check 场景声明；新增 nested 测试也移除不适用的 standalone-review 声明 |

另外，一次恢复外层遗漏 PATH 中的 Codex 安装目录，导致 bootstrap 失败；修正的是启动环境，不把这次人为错误当作业务或 Host schema 缺陷。期间还有执行端中断/额度问题，中断测试日志没有计入通过结果。

因此，后续最值得改进的执行方法是：先核实保留接口和任务范围，再运行长流程；在正式审查前检查集成；让失败回归覆盖真实触发和跨层恢复，而不是只覆盖最简单的一层。上述方法建议不是本次已经交付的新强制能力，也不代表新增了自动范围拒绝器或自动冲突修复器。

## 11. 最终验证与仍保留的问题

### 11.1 最终已完成的证据

| 阶段 | Invocation | 结果 |
| --- | --- | --- |
| 最终 dev-loop | `0018d8cb-03ba-4649-85f8-d858fd50c394` | `succeeded / ready`，六项配置检查全部通过 |
| 补充独立 Harness 及共享模块审查 | `a8c95dad-1948-4453-9cd5-1bc78e40d1e0` | `succeeded / completed`，四个 Module 均无 blocking、无 gap |
| 正式 source delivery | `46d58f4b-978c-4af4-bd64-bd71d690d06c` | `succeeded / delivered`，七项集成检查通过，源工作树清理完成 |
| 正式 main 合并 | `d262ea4b-5ca9-4ebc-893b-89c4646fe9b2` | `succeeded`，七项检查再次通过，main 指向 `00633382` |
| 合并后生成同步 | 2026-09-12 00:14 UTC | build、build --check、diff --check 均退出 0；源文件、HEAD、index 未变化 |

main 合并阶段的配置检查明细：

| Check | 实际完成 |
| --- | --- |
| `check.spec.model` | 42 项测试通过 |
| `check.harness.runtime` | 80 项测试通过 |
| `check.development.runtime` | 132 项测试通过，零失败、零错误、零跳过 |
| `check.views.publication-types` | TypeScript 检查通过 |
| `check.views.repository-regressions` | 144 项 TypeScript 测试、58 项 Python 测试及相关构建通过 |
| `check.views.ua-graph` | 12 项测试通过 |
| `check.views.viewer` | 7 项测试通过 |

这些检查存在覆盖重叠，不能直接把数字相加当作独立测试总数。“全部通过”指上述实际配置和执行的检查，不是声称穷尽整个系统、所有运行时或所有平台。

### 11.2 没有把 advisory 冒充修复完成

最终生命周期审查记录 12 项 advisory：Views Spec 2 项、Views code 3 项、Spec code 1 项、Development code 0 项、Reflections code 6 项。补充独立审查中 Harness 和 Development 为 no_findings，Spec 和 Distribution 各有 1 项 advisory。不同审查中的重复问题不算独立新增缺陷。

主要保留问题包括：

- Spec 文本中 Profile 10/11 的既有矛盾。
- Views 的 dependency 描述未完整表达 Distribution 对 publication projections 的供应责任；一条 requirement 合并了两个禁止行为。
- scaffold 对被修改 proposal 的目标/清单校验和并发创建边界存在既有缺陷。
- viewer runtime admission 对中间 symlink 路径覆盖不完整。
- Distribution 重建失败时保留旧 runtime 的既有问题。
- Reflections 的文档归属、处置、重复调查、approval 复用、过期证据测试及标题注入检查等独立问题。

其他轮次还记录过 Markdown 长围栏解析等问题；最后一轮未重复提及，不构成它已修复的证明。这些问题没有通过删日志、改 severity 或把任务无限扩大来处理。本文只报告它们的状态，不创建 Reflection，也不启动这些独立修复。

### 11.3 工作树、生成文件和证据的边界

全过程在需要时通过同工作树 fresh 维护/正常会话交接，保持唯一写者。修改已加载 Skill 相关源时不在旧会话继续编辑，生成输出由 build 产生。原有 AGENTS/CLAUDE 修改在源存在期间保持原字节，不进入交付提交；最终由正式 delivery 清理源工作树。

源码或 HEAD 变化后重新取得相应验证和审查证据。外层暂停、人工停止 worker、维护测试通过、旧的 ready 都没有替代当前 Host 的正式结果。最后两个交付动作分别保留回执，source delivery 并未被冒充为已经完成 main 合并。

## 12. 提交与证据索引

| 主题 | 主要提交 |
| --- | --- |
| 普通文件 sandbox 适配 | `1c5773df` / `e69938a8` |
| graph view 删除与早期回归 | `5b1c4cfb`、`c46a82b8` |
| Node 绑定及初始 task-scope repair | `f2c5f7e2` / `80088c3c` |
| worker/Host 验证职责 | `c32abbca` / `4c451a0e` |
| 保留接口格式纠正 | `1959577d` |
| 审查范围与 gap 输入新鲜度 | `74bd2564` / `77db1e6f` |
| 撤回额外历史别名机制 | `4c978363` |
| 历史任务身份输入 | `a8a0ab0b` / `afeb5043` |
| 冻结清单内搜索 | `2de47801` / `c0c13560` |
| Node 测试夹具 | `15626fc8` / `f65a93d7` |
| 任务控制值合同 | `c4b9f41d` / `355ca24d`、`9b001d91` / `ac75849e` |
| 协调 scope repair 与稳定 review 身份 | `90fbdf92` / `87c8c0b6` |
| 导航及 viewer 验证纠正 | `adfb6a08` |
| task-control 错误及副作用测试 | `e53a9037` |
| tasks-only 与直接子组件 resolved gap | `efcd5921` |
| 当前文档链接语义 | `2e24100a` |
| 链接实现、范围指引、冷检查等 19 文件 checkpoint | `fb2a7641` |
| 集成 main 并保留双方内容 | `cf52368b` |
| 条件准入、嵌套缺口归属及测试声明 | `00633382` |

表中的斜杠表示 main 与候选上的对应维护批次，不声称它们都是字节完全相同的 cherry-pick。部分差异是两边各自测试或配置必须保留的内容。

相对原始基线 `48f9581e03d73bd3662dd389cf21a247a6e3db21`，最终代码树共变化 79 个文件；相对合并前 main `9b001d91`，本次最终集成带来 45 个文件的差异。两种口径不同，均包含必要的测试和 Spec 修改；79 文件口径也包含并行写入 main 的 R-073/R-074，不能全部算作我的新增修复。

可复核命令：

```bash
git show 00633382
git diff --stat 9b001d91 00633382
git diff --stat 48f9581e 00633382
git show cf52368b --format=fuller --no-patch
```

本报告附带 [证据摘要 JSON](2026-09-12-docsite-dev-loop-evidence.json)，保留最终 invocation、检查结果、审查原始 finding 和关键回归结果。该 JSON 是报告附件，不是 Framework wire contract 或 Reflection 记录。

本机的完整 [交付/合并回执](../../.concorde/deliveries/change.5168b485-c195-417f-8ecb-5861cd9183f9.json) 及 [main 集成检查日志](../../.concorde/deliveries/change.5168b485-c195-417f-8ecb-5861cd9183f9/primary/) 仍可核对；它们是本地控制数据，不保证随 Git 分发。源工作树的生命周期目录已按 delivery 清理，因此报告附件保存了必要摘要，避免读者只能依赖已经删除的源目录或临时日志。
