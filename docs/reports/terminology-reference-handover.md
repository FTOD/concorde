# Handover：全项目 Spec 术语引用与链接修正

## 1. 新 session 的工作目录与任务

- 初始工作目录：`/home/zhenyu/concorde`。
- 当前分支：`main`；继续在这个工作树直接维护，不创建、切换或进入其他工作树。
- 检查基线：`19cc893775777f399c19d89ea430be27aa0d9212`。
- 基线提交：`docs(development): distinguish capability dispatch from worker execution`。
- 写本交接前工作区干净。上一轮术语审计是只读的，**尚未修正下述遗漏**。
- 用户已同意下述修正规则，并要求在新的 session 中执行修正。本 session 只保存交接，不实施修复。
- 本文件是工作交接，不是注册 Spec，也不是新的规范来源。项目 Specs 仍须使用 English；交接和对话可以使用中文。

请先读取并遵守当前 `AGENTS.md` 和完整的 `.concorde/protocol/principles.md`，再确认实际 Git 状态。
这是直接维护，不要自行启动 Concorde 的开发、审查、验证或交付 flow，也不要因为任务较大而自行委派 subagents。
按项目政策格式化、验证并提交已确认的修正；不 push、不部署、不做交付或主分支合并操作。

## 2. 用户的问题与已同意的方向

用户发现 `specs/concorde/development/review-and-gaps.md` 使用了 Issue，却没有链接到 Issues 的解释，问是否应直接链接 `specs/concorde/issues/module.md`，并要求检查整个项目类似遗漏。

用户随后同意这些修正规则：

1. **逐页选择理解本文必需的术语**，不要按 Module 套固定词表。
2. **Terminology 直接链接到 canonical 定义表**。正文首次讨论另一个 Module 的能力或职责时，补该 Module 的入口链接。
3. **不需要每次出现都链接**。建立清楚的入口后保持自然阅读，去掉不相关的词表项。
4. **先消除歧义，再链接**。不要把普通词或同名的另一种概念机械链接到错误定义。

目标读者懂一般软件开发，但不知道 Concorde 的实现。修复应改善实际理解和导航，不是把全文变成链接墙。
此次任务覆盖全部 17 个 Modules 的注册 Specs，包括解释页和 Implementation Specs；不能只修用户举出的页面或下方的示例清单。

## 3. 当前结构和已有工作的边界

当前 Protocol 为 **9.0.0**，文档 metadata 为 **schema 2**，Framework Profile 为 **14**，registry schema 为 **5**。

- Module 入口顺序：Purpose → Terminology → Usage → Design → Relationships。
- 解释性专题页：简短导语后先给 Terminology。
- `document.role: module` 是解释性内容；`implementation` 是精确规范。
- 正式 Requirements、Scenarios、canonical structured contracts 和精确 executable Flow catalog 不放在解释页。
- 文档 ownership、context inclusion、Module composition、capability use 和 implementation file bindings 是不同关系。
- 链接仅供导航，不会自动扩展 agent context。必需的术语定义单元需要显式 references。
- Term 表不是 entity inventory；实体具体职责仍在 Design/Relationships 等上下文中解释。

已有改动：

- `6e07e514`：全项目迁移至 Protocol 8 的两种文档角色。
- `c9871160`：Protocol 9、Terminology、解释优先的正文改写和精确执行参考分离。
- `19cc8937`：修正 Development 的关系图，必须保留这个已确认的模型：
  - Development host → Development capabilities：`dispatches admitted requests to`。
  - Development host ⇢ Harness：`prepares and runs worker invocations through`，仅在需要模型执行时发生。
  - Capability 可以是普通代码、模型调用或组合；Harness Module 也提供隔离检查等其他服务，不能等同于“一切工作都是 worker”。

**本轮已有 Protocol 原则足够表达术语引用规则。无需默认再升级 Protocol、引入 metadata 字段或重构执行模型。**
如果确有规则缺口，先说明具体原因，不要用格式变更替代编辑工作。

## 4. 审计范围、方法及可信度

基线 registry 共 **17 个 Modules、113 个文档单元**：53 份解释性单元、60 份精确规范单元。
静态检查从真正的 `Term / Meaning / definition` 表中提取了 **60 个 canonical 术语名**，比较正文用法、本页词表和已存在的直接定义链接，并人工复核了主要解释页。

注意：

- 全量扫描产生的是候选，不是每条都已确认的缺陷。普通词、偶然提及、Module 名称和概念别名需要语义判断。
- 不要把“所有没有链接的匹配词”视为必须新增的表项。
- 只解析实际的 Terminology 词表及连续表格行；不要把整个 section 下其他字段表、状态表都当成术语定义。
  Implementation Specs 中可能存在较低级子标题，简单收集 section 中每个表格行会产生大量假定义。
- 排除代码围栏、代码标识符、链接目标、正式定义标题和 metadata。处理词组、单复数和跨行文本时仍需人工判断。
- 某页已有普通 API 链接或某个指向 `concepts.md` 的链接，不等于它已经为另一个具体术语建立了定义入口。

临时文件曾保存在 `/tmp/concorde-terminology-audit.py`、`/tmp/concorde-terminology-audit.json` 和
`/tmp/concorde-terminology-review.md`。它们可能仍存在，但**本交接不依赖这些临时文件**；不要未经复核将候选表直接转换成编辑。
下一 session 应以当前 registry 和源文件重建索引。

## 5. 起因页面：Issue 与 Blocker

`development/review-and-gaps.md` 开头是：

> An Issue records a problem. A blocker records that a particular task cannot continue because of that problem.

正文反复谈 Issue/Blocker，但 Terminology 表却是 Capability、Host、Flow、Candidate、Evidence：
**核心术语漏掉了，而若干表项与该页实际内容不相干。** 页面也没有给出 Issues Module 的入口链接。

当前 canonical 状态：

- `Issue` 和 `Blocker` 都定义在 `specs/concorde/concepts.md#terminology`。
- `specs/concorde/issues/module.md#terminology` 目前只是导入它们，并不是它们的 canonical 定义表。
- 因此，直接链接 Issues Module 很适合作为“了解 Issues 的能力和职责”的导航，但目前不能冒充 Issue 的直接 canonical 定义链接。

最小且符合当前规则的修正：本页词表导入 Issue/Blocker 的真实定义，并在相关正文补 Issues Module 的入口链接。

讨论中还提出了一个可选组织改进：领域术语 Issue 的 canonical 定义可以迁入 Issues Module 的 Terminology，让其他页面直接到责任所属处，而全局 concepts 页作为入口。
**这不是本轮必须进行的全局定义迁移。** 不要仅为补一个 Module 导航就大规模搬动词汇所有权。
若采用该方向，必须一次性迁移唯一的定义、所有导入链接和必要的显式 references，不能建立两个定义或“词表转发到另一个词表”的链。
Blocker 是任务对问题的依赖关系，其责任可能在 Development；不要因为它引用 Issue 就把它也直接塞进 Issues。

## 6. 已确认的优先修复示例

以下路径均相对于 `specs/concorde/`。它们是起点，不是穷尽清单。
“缺少定义入口”不等于该页没有任何相关链接。

| 页面 | 需要检查并补充的术语 | 当前 canonical 定义表 |
| --- | --- | --- |
| `development/review-and-gaps.md` | Issue、Blocker | `concepts.md#terminology`；Issues 行为入口是 `issues/module.md` |
| `harness/graphs-and-loops.md` | Flow，页面主题本身就在讲它 | `concepts.md#terminology` |
| `harness/host.md` | Host、Flow、Skill | `concepts.md#terminology` |
| `harness/module.md` | Spec context、Implementation context、Capability context、Task context | `harness/context.md#terminology` |
| `harness/execution.md` | worker 报告问题时使用的 Issue | `concepts.md#terminology`，并考虑 Issues Module 导航 |
| `spec/module.md` | Protocol binding | `spec/values.md#terminology` |
| `views/publication.md` | Document role、Promotion | `spec/values.md#terminology`、`views/pipeline.md#terminology` |
| `planning/module.md` | Acceptance task、Spec context | `planning/tasks.md#terminology`、`harness/context.md#terminology` |
| `issues/module.md` | Disposition | `issues/lifecycle.md#terminology` |
| `distribution/module.md` | Protocol binding | `spec/values.md#terminology` |
| `distribution/build.md` | Public capability | `development/module.md#terminology` |
| `views/ua-graph.md` | Implementation context | `harness/context.md#terminology` |

精确规范也有类似问题：

- `harness/contracts.md` 使用四类 context、Capsule、Issue 等，但没有完整导入相应术语定义。
- `views/contracts.md` 使用 Document role、Promotion，但词表仍主要是通用的 Module Specs、Implementation Specs、Registry。
- 其他入口及专题常漏 Host、Worker、Evidence 等理解其行为所需概念。请逐页判断是否真正需要，不要全部机械添加。

明显不相关的复用表项示例：

- `development/review-and-gaps.md` 的 Capability、Host、Flow、Candidate 未承担该页的核心概念介绍。
- `harness/graphs-and-loops.md` 列 Worker、Harness、Context、Grant、Snapshot，却漏 Flow。

## 7. 已有 canonical 位置速查

请以实际源文件复核，不要把此表当成第二份定义。

| 定义文档 | 术语 |
| --- | --- |
| `concepts.md` | Module、Spec、Module Specs、Implementation Specs、Entity、Requirement、Scenario、Registry、Context、Grant、Snapshot、Evidence、Capability、Skill、Worker、Host、Harness、Flow、Candidate、Worktree、Ready、Delivery、Issue、Blocker、Contract |
| `spec/registry.md` | Ownership、Composition、Use、Reference、Implementation binding |
| `spec/values.md` | Document unit、Document role、Source-member role、Protocol binding |
| `spec/structure.md` | Structural validation、Semantic completeness |
| `spec/initialize.md` | Initialization、Initial proposal |
| `harness/module.md` | Worker profile、Tool gate、Capsule |
| `harness/context.md` | Spec context、Implementation context、Capability context、Task context |
| `development/module.md` | Public capability、Internal capability |
| `issues/lifecycle.md` | Disposition |
| `distribution/installation.md` | Installation、Update、Installation receipt |
| `views/pipeline.md` | Publication candidate、Promotion |
| `planning/assessment.md` | Task sufficiency |
| `planning/tasks.md` | Acceptance task、Reserved task ID |
| `review/module.md` | Review coverage、Advisory finding |
| `delivery/module.md` | Delivered branch、Delivery receipt |

每一个 canonical 链接都应指到这些文档的 `#terminology`，而不是一个只再转发的词表。

## 8. 必须人工处理的歧义

- `Candidate`：开发候选变更，与 `Publication candidate`（待发布网站）不同。Views 里不能一见 candidate 就链接到 worktree 概念。
- `Spec`：可能指规格文档，也可能是 **Spec Module**。必要时明确写出后者并链接入口。
- `Harness`：通用 worker 执行机制与 **Harness Module** 的较宽职责不完全重合，保留已确认的 Capability 分派模型。
- `use`、`reference`、`update`：普通动词不一定是 Registry 的 Use/Reference 或 Distribution 的 Update 术语。
- context 文件的 `delivery` 不一定指 Delivery capability。
- `Issue` 是问题记录，`Issues Module` 是提供相关行为的责任；`Blocker` 不是 Issue 的另一个名字。
- 源码函数名、字段名、示例中的应用领域词，不必全部升级为项目 canonical 术语。

## 9. 现有校验的盲区与相关代码

当前校验主要检查**已经存在的链接是否正确**，没有检查“正文依赖一个术语但根本没有导入/链接”，也没有检查表项是否相关。
所以现有检查通过不代表本次问题已解决。

相关实现：

- Python 表结构与早期位置：`src/concorde/spec/content_model.py` 的 `terminology_body`、`terminology_problems`。
- Python canonical/context 检查：`src/concorde/spec/validation.py` 的 `terminology_findings`。
- `src/concorde/spec/content_repository.py` 的整体校验也使用这些结果。
- TypeScript 表结构：`docsite/plugins/scoped-content/reading-format.ts` 的 `terminologyBody`、`requireTerminology`。
- TypeScript canonical/context 检查：`docsite/plugins/scoped-content/model.ts`。

已有测试入口：

- `tests/concorde/spec/test_content_model.py`
- `tests/concorde/spec/test_content_repository.py`
- `docsite/tests/contract/document-unit-format.test.ts`
- `docsite/tests/scoped-registry.test.ts`
- `docsite/tests/repository/framework-guides.test.ts`

可增加帮助发现遗漏的审计和回归，但不要直接把关键词匹配变成“所有词都必须链接”的硬失败条件。
优先让作者/审查检查“本页实际用到的关键概念 → 唯一定义位置 → 本页明确入口”，保留对普通词和歧义的语义判断。
如果修订作者或审查 prompt，遵守生成规则并重建，不直接编辑 generated 或已渲染 Skills。

## 10. 推荐执行顺序

1. 确认 cwd、分支、HEAD 和工作区；读取项目政策和 Protocol，确认未有他人改动。
2. 从 `.concorde/specs.json` 枚举所有 owned document units，读取 metadata role 和正文，建立真实 canonical 术语索引。
3. 逐页核对理解该页所需概念，区分术语定义链接和 Module 能力导航，先修上述高优先级问题。
4. 检查其余全部 Module Specs，再检查 Implementation Specs，去掉不相关词表项、补必要导入和首次使用导航、消除歧义。
5. 对新增跨文档定义引用核对每个受影响 Module 的显式 references，保持一层展开语义；不得靠 Markdown 链接隐式补读。
6. 若移动 canonical 定义，统一修复所有导入与上下文。保持文档、实体、requirement/scenario、contract 身份和 Module 所有权，不因编辑顺手重命名。
7. 补适当回归并运行结构、上下文、链接、构建测试。用浏览器从 `review-and-gaps` 验证读者能到正确的定义及 Issues 入口；抽查其他 Module。
8. 格式化、复读 diff、复验最终字节、确认第二次格式化 no-op、检查 staged diff、提交、确认工作区干净。

交付时说明：覆盖了哪些文档、术语定义是否迁移、哪些歧义被明确、新增/调整了哪些 references，以及测试结果和未解决问题。
不要把静态扫描候选数量当作确认缺陷数量，也不要声称机器测试证明可读性完备。

## 11. 验证命令与环境

在 `/home/zhenyu/concorde` 执行，直接维护使用 CLI 验证而非 `concorde-validate` flow：

```bash
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
python3 scripts/development/check-spec-v5.py --base 19cc8937
.venv/bin/python scripts/development/check-flow-specs.py
python3 scripts/development/run-tests.py -j 8
CONCORDE_PYTHON="$PWD/.venv/bin/python" npm --prefix docsite run check
```

若修改 `prompts/`、`skills/`、`capabilities/` 或 wire contracts，先 `python3 scripts/concorde.py build`。
仅在确实授权并修改 Protocol 时才需要重算 manifest/显式绑定，不要为了普通链接修复升级 Protocol。

注意：系统 `python3` 没有 LangGraph；Flow 检查用 `.venv/bin/python`，docsite 完整测试/构建设置 `CONCORDE_PYTHON`。
Python 并行 runner 比串行 discover 更合适；以前串行全量曾在 10 分钟超时，不能将超时当成通过。

历史验证基线（不是新修复的证据）：

- Protocol-9 改写：Python 844 项，0 失败，10 项可选 Studio Server 测试跳过；docsite 222 项通过。
- 最新 `19cc8937` 图修正：docsite 223 项通过，类型检查、生产构建、Spec/Flow 校验和身份/链接审计通过。

格式化必须遵守 AGENTS：Pi 可能延迟写入，不能只在提交前看一次 status。
之前环境给 TS/JSON 选择 Biome，给 Python 选择 Ruff；使用新 session 的实际有效配置、每个文件原有缩进并只格式化改动文件。
不要为了消除遗漏而关闭 broken-links、Terminology 或 context 检查。

## 12. 完成标准

- 用户指出的 Issue/Blocker 页面已有清楚的定义入口与 Issues Module 导航。
- 所有注册文档均经过逐页术语相关性检查，不只是批量复制一组链接。
- 必要的外部术语直接指向唯一 canonical 表；无重复定义、转发链或依赖隐式读取。
- 引用其他 Module 的行为时有合适的入口导航；不要求每次重复出现都带链接。
- Publication candidate、Spec Module、Harness Module 等歧义得到正确区分。
- 原有软件义务、stable IDs、执行 Flow 和安全限制不因术语整理而改变。
- 最终检查通过并提交；最终答复不声称已部署线上。
