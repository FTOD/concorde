# Spec Protocol 3.0 迁移：问题与设计决定

日期：2026-09-09。规范依据：Spec Protocol 3.0.0（本次制定）。

这是一次开发者直接授权的维护记录，不是注册的 Module Spec，不加入任何 Module 的上下文，
也不使用 Reflection 系统。项目处于快速迭代阶段：本次迁移不保留对 Protocol 2.x、Profile 9
或 registry schema 2 的兼容，允许舍弃部分功能，以改完之后与新 Protocol 相符为准。

## 范围与结果

- Spec Protocol 升级到 3.0.0：只保留一种 Spec（Module Spec），删除 Implementation Spec。
- 每个 Module 的主 Spec（`module.md`）必须有四个部分：Purpose、Scenarios、Entities、
  Architecture。前两部分是功能规格，后两部分是架构规格。
- Feature 和 Interface 不再是注册实体。行为用 Scenario（GIVEN / WHEN / THEN）和 SHALL
  Requirement 表达；接口成为架构里的 entity，其行为由 scenario 说明，结构化值仍用
  `concorde-contract`。
- 实现文件成为 Module 的元数据：每个 entity 可以列出它绑定的文件，Module 的文件集合是所有
  entity 文件的并集，注册表的 `files` 字段镜像这个并集，校验器核对两边一致。
- Framework 配置升级到 `profile_version: 10`、registry schema 3、workspace protocol 15。

## 已采用的设计决定

### D01：功能规格用 Scenario 和 Requirement 表达

Scenario 是带稳定 ID 的标题（`### scenario.x.y — Title`），下面是以 GIVEN、WHEN、THEN、AND、BUT
开头的列表项。Requirement 是 `- req.x.y: ... SHALL ...` 形式的列表项，写在 scenario 内属于该
scenario，写在别处属于整个 Module。Scenario 可以用普通标题分组，分组没有身份。Scenario 和
Requirement 只能定义在单一 Module 拥有的文档里；共享文档不能定义它们。

### D02：接口是 entity，行为是 scenario

接口不再有 `interface.*` 身份。它作为架构里的一个 entity 出现（kind 自由，例如 interface、
command、file format），使用者作为边界外的 entity 出现。输入、输出、错误、重复调用等行为
分别写成 scenario 或 SHALL requirement。结构化值的约定仍用 `concorde-contract` 块。

### D03：Entity 携带文件绑定，Implementation Spec 删除

`concorde-entities` JSON 块声明 Module 的 entity：`id`、`title`、`kind`、`responsibility`
必填；`files`、`pending`、`target_id` 可选。`target_id` 必须是本 Module 的子 Module 或 `uses`
目标，且不能同时带 `files`。一个文件可以被多个 Module 列出（共享代码），在一个 Module 内只能
属于一个 entity。文件不能是 Spec 文档、`generated/` 或 `.concorde/` 控制记录。

Module 的 implementation context 就是其 entity 文件的并集。只有代码阶段读到文件内容；
planner 等只读 Spec 的阶段看到文件名（它们本来就在 module.md 里），看不到内容。

旧的 21 个 Implementation 文档折叠为 entity 的 `responsibility`，未决事项迁入各 Module 的
Unresolved 节，验证义务由 scenario 和注册表 `checks` 承担。

### D04：Pending 文件与交付确认

entity 可以在 `pending` 里列出已声明但尚未创建的文件。校验器对未标 pending 且不存在的文件报错，
对已存在却仍标 pending 的文件只报 warning。code writer 不修改 entity 元数据；`plan`/`tasks`
阶段先声明 pending 文件，代码阶段的写权限集在执行前固定。交付时 host 验证物理文件存在，
删除对应的 pending 标记并把这次确定性修改纳入交付提交。这与"不存储状态字段"的原则的关系：
pending 是作者声明的意图，不是证据；文件是否存在始终由校验器实时核对，标记只在交付时清除。

### D05：Mermaid 图与 entity 一致

`module.md` 的 Architecture 节至少有一个 Mermaid flowchart。图中节点标签（`<br/>` 之前的第一行）
的集合必须等于 entity 标题集合；每条边必须有标签，标签就是关系动词。图是关系的唯一权威，不再
另写关系列表。外部图源（Archify JSON、注册表 `diagrams` 声明）整体删除：图只存在于注册的
Markdown 文档里，Context(M) = D(M)。

### D06：查询域与归属

可查询的实体是 Module 和 Scenario；Scenario 解析到其提供 Module 的完整上下文。Reflection 的归属
必须是 Module ID 或 Scenario ID。Entity 和 Requirement 是 Module 内的定位，不是独立查询。

### D07：结构与内容的分工

注册表记录结构：Module 身份、文档成员、parent、uses、files、checks。文档记录内容：scenario、
requirement、entity、dependencies、contract。普通 Spec 作者可以改 entity 的描述，但改文件
列表属于拓扑变更（注册表 `files` 必须同步），由 topology 流程完成。

### D08：舍弃的功能

- Implementation Spec 及其文档、code writer 维护 Implementation 文档的权限路径、honest stub 生成。
- Feature/Interface 注册项、`interface.*`/`feature.*` 身份。
- 外部图源、Archify JSON overview、`generated/diagrams` 输出、`diagrams` 注册字段。
- Profile 7 legacy `understanding` 包保留在仓库里（pending removal），只作为 `module.views`
  的一个 entity 列出；它不参与任何 Profile 10 路径。（后记：该包连同 alignment explorer 已在
  提交 2426f5a3 删除，不再是任何 Module 的 entity。）

### D09：目录前缀绑定（Protocol 3.1.0）

entity 的 `files` 条目可以是精确文件，也可以是以 `/` 结尾的目录前缀；目录前缀绑定其下现有和将来
的全部普通文件（Framework 排除 `node_modules`、`__pycache__`、`.venv`、`build`、`dist`、点开头的
目录和文件、`.pyc` 与 `.log`）。同一 Module 内多个条目覆盖同一文件时最具体的条目拥有它：精确文件
优先于目录，长目录优先于短目录。跨 Module 的重叠是共享列出。目录前缀不能包含注册的 Spec 文档。
注册表 `files` 仍是条目并集；`pending` 可以标记尚未创建的目录。上下文快照升到 schema 3，增加
`implementation_entries`（声明的条目）并把 `implementation_files` 改为展开后的文件名；code writer
在已列出的目录下新建文件不再需要预先声明 pending。项目自身的代码此前已按 Module 重排为一包一
Module，所以每个 Module 的包目录和独占目录用一个前缀列出，共享文件仍精确列出。

## 涉及的实现改动

Protocol 文本与模板、`prompts/protocol/framework-profile.md`、`.concorde/constitution.md`、
`.concorde/config.json`、`.concorde/specs.json`、`src/concorde/spec/*`、
`src/concorde/development/{capability_host,review}.py`、`src/concorde/harness/worktree_delivery.py`、
`src/concorde/distribution/{package_validation,build,cli}.py`、`src/concorde/reflections/*`、
Agent 指令、Skills、workflow prompts、docsite scoped-content 插件、
全部项目 Specs 及测试。

## 实现备注

- Python 源码与测试按 Module 分包：`src/concorde/{spec,harness,development,distribution,reflections,views}/`
  与 `tests/concorde/<module>/`（每个 Module 一个扁平测试包），共享文件放在排序靠前的那个 Module 的包里，
  但仍由每个使用它的 Module 的 entity 列出；`src/concorde/{host,specification,autodocs}` 不再存在。
- 解析器把列表项的懒续行（缩进的下一行）并入同一步骤或 requirement，所以换行书写的 GIVEN/WHEN/THEN
  和 SHALL 句子都可以正常解析。
- `_implementation_users(target)` 返回 `{target} ∪ affected_modules(target.files)`，没有文件的 Module
  仍然跑自己的 `checks`。
- 一个 Module 的 implementation context 只是它自己的文件列表：另一个 Module 新列出同一文件不会使
  已冻结的代码阶段上下文失效，只会扩大反向索引。
- docsite 的 build manifest 升到 schema 17，只发布 Module 页面，每页附 Files 列表；Mermaid 由
  `@docusaurus/theme-mermaid` 在客户端渲染。
- 校验器输出的 `CONCORDE-ENTITY-005`（stale pending 标记）和 `CONCORDE-ENTITY-006`（未被任何
  Module 列出的源码文件）是 warning，不影响 `validate` 的成功状态。

## Protocol 4.0.0（2026-09-10）：Ontology、Module 级 Requirement、锚点、测试声明

同样是开发者直接授权的维护记录。触发原因是开发者对 3.1.0 的四点修订意见；快速迭代期不保留对
Protocol 3.x、Profile 10 的兼容。Framework 配置升级到 `profile_version: 11`，registry schema 3、
workspace protocol 15 不变，constitution 升到 16.0.0。

### D10：Ontology 大节包住 Entities 和 Relationships

`module.md` 的四个必需部分改为 Purpose、Requirements、Scenarios、Ontology（顺序固定，标题级别
1–3）。Ontology 之下必须各有一次、按序出现 Entities（含 `concorde-entities` 块）和 Relationships
（含 Mermaid flowchart）两个子节，级别比 Ontology 深。名字坚持用 Ontology（本体论 / 世界观）：
Module 领域里存在什么、它们之间如何关联；Protocol 正文用一段话解释这个词，不要求任何形式化的
本体语言，程序和文件与业务概念一样属于它。Purpose、Requirements、Scenarios 是功能规格，
Ontology 是架构规格。原 "Architecture" 一名在 Protocol 与校验器里不再作为节名出现。

### D11：Requirement 只属于 Module，是标题节

Requirement 是 `### req.<module>.<name> — Title` 形式的标题节（级别 2–5），标题后第一个段落是
statement：一句话，恰好含一个 `SHALL` 或 `SHALL NOT`；后面的段落是解释，不被解析。三条质量规则：
一条只表达一个行为（校验器按 SHALL 出现次数判）、可判真伪（spec_reviewer 审）、名称稳定唯一
（ID 即身份）。开发者撤回了"描述结果不描述实现"的规则，因此 Requirement 可以规定技术选型（例如
控制流必须是 LangGraph 图），不设单独的 Constraints 类别。`- req.x:` 列表项在任何位置都是错误。

Scenario 节只允许 GIVEN/WHEN/THEN/AND/BUT 步骤和普通段落，不再有 scenario 级 requirement：原先
挂在 scenario 下的 SHALL 句并入该 scenario 的步骤或说明；跨情景成立的承诺提升为 Module 级
requirement。Scenario 与 requirement 之间不设引用关键字。Requirement 与 scenario 的粒度不同：
requirement 是粗粒度的需求，scenario 是具体可测试的情景。

### D12：锚点等于 ID

每个 scenario、requirement、entity 的 ID 就是它定义处的锚点：`harness/module.md#req.harness.x`
这样的普通 Markdown 链接可以直达定义。路径是定位符，改名或搬文档不改变身份；片段是稳定部分。
校验器规则 `CONCORDE-LINK-001`：片段形如 `scenario.`/`req.`/`entity.` ID 的本地链接必须指向定义
该 ID 的文档，未定义的 ID 是错误；其他片段不解释。docsite 物化页面时给 scenario 与 requirement
标题追加 `{#id}` 显式锚点，并在每个 `concorde-entities` 块前插入 `<a id="entity.x"></a>`。
Purpose 等固定节不另设 ID，由 Module ID 加节名定位。

### D13：测试声明 scenario，Spec 不列测试

Protocol 只规定方向和身份：声明写在测试里、以 scenario ID 命名、绝不出现在 Spec 文档中；具体语法
由工具按语言定义并须不执行测试即可读取。Framework 的 Python 约定是
`concorde.spec.verification.verifies` 装饰器：`@verifies("scenario.harness.context-freeze")`，
可列多个 ID。校验器用 `ast` 解析各 Module 列出的 `.py` 文件建立 scenario → tests 反向索引：
未知 scenario（`CONCORDE-VERIFICATION-001`）和无法解析的 Python 文件（`-004`）是错误；无测试声明
的 scenario（`-002`）和声明所在文件未被该 scenario 所属 Module 列出（`-003`）是 warning。覆盖率
是关于测试的证据，不是契约的一部分；没有测试的 scenario 仍是 Module 的承诺。

### D14：迁移方式

脚本完成机械部分：`module.md` 标题重排、Module 级 `- req.` 项转为标题节、scenario 内 `- req.` 项
转为该 scenario 的段落、版本与节名短语替换；然后每个 Module 由一个独立代理润色：拆分双 SHALL、
补标题、把 scenario 段落并入步骤或提升为 Module requirement、修正描述旧布局的散文。测试侧由每个
Module 的代理给现有测试补 `@verifies` 声明，只标注明确覆盖某个 scenario 的测试。

### D15：Module 是规格单元，不是实现单元（2026-09-10 澄清）

Module 不必对应任何物理实体：不要求有对应的包、目录、进程或服务，其实现可以分散在多个物理单元、
与其他 Module 共享，或完全由子 Module 提供；承诺完全由子 Module 兑现的 Module 自身不绑定文件。
Module 的边界由 purpose、requirements、scenarios 和 entities 确定，文件绑定只记录责任在哪里
被实现，不定义边界。Protocol 此前处处暗示这一点（P2 的目录列表不构成边界、空 implementation
context 的定义、composite Module 可有自身协调代码），但从未正面陈述；Concorde 自身的根 Module
零文件、`module.spec` 横跨多个目录，已是这种形态。本次在 P1 与 Module 章开头各补一段正面定义，
不引入 "domain" 作为术语（Ontology 章已用该词指 Module 的世界）。这是澄清而非规则变化，版本
保持 4.0.0，`protocol/manifest.json` 摘要与 `.concorde/config.json` 的 Protocol 绑定随之刷新。

### 涉及的实现改动（4.0.0）

`protocol/`（principles、module、format、spec-management、spec-and-context、README、两个模板）、
`protocol/manifest.json`、`.concorde/config.json`、`.concorde/constitution.md`、`concorde.json`、
`scripts/install-concorde.py`、`src/concorde/spec/{repository,validation,initialize,verification}.py`、
`prompts/protocol/framework-profile.md`、Agent 指令（spec_author、spec_reviewer、task_author、
implementation_worker、code_reviewer）、`skills/concorde-validate/SKILL.md`、docsite 插件
（`model.ts`、`materialize.ts`）及其测试、全部项目 Specs、Python 测试与 golden fixtures。
