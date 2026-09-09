# Spec 修订：问题与设计决定

日期：2026-09-09。规范依据：Spec Protocol 2.0.0。

这是本次直接维护的工作记录，不是注册的 Module/Implementation Spec，不加入任何 Module 的
上下文，也不使用 Reflection 系统。以下决定已直接写入项目 Spec；标为“实现待跟进”的条目
不代表代码已经实现或验证通过，不需要等待用户逐项确认才能完成本次 Spec 修订。

## 范围与结果

- 阅读并修订现有注册项目 Specs，覆盖 14 个 Module、18 个 Implementation Spec、65 个注册
  Markdown 文档；59 个文档发生修改或新增，6 个配套文档审阅后保留。
- 删除当前项目 Specs 的 12 个外部架构 JSON 源，把实体关系模型写入各自 `module.md`。
  原先没有图的 Wire Contracts 和 Viewer 也补上 Mermaid；现有开发、拓扑状态图保留并补齐源声明。
- `.concorde/specs.json` 同步更新图声明、依赖和新增文档成员；项目 Constitution 补上 Mermaid 约定。
  Module、Feature、Interface 和 Implementation 的既有稳定身份及实现文件绑定保持不变。
- Spec Protocol 本身及其 `protocol/` 章节、模板和 manifest 未在本次修改。
- 运行时代码、安装脚本、作者指令、依赖锁和历史测试夹具未在本次迁移。因此本次完成的是
  **Spec 层的 Mermaid 迁移与契约修订**，不是宣称仓库所有运行时 Archify 依赖已经清除。

## 已采用的设计决定

### D01：图的权威源放在 Markdown 内

问题：外部 JSON、生成 HTML、registry recipe 和正文中的图引用形成了多套需同步的表示。

决定：每个 Module 的 `module.md` 在 `Architecture` 下包含 Mermaid fence，旁边声明完整源路径、
`kind: mermaid` 和标题；图内提供英文 `accTitle`、`accDescr`。图与文字共同说明同一个模型。
图的源是整个注册 Markdown 文档，不新增隐藏文件，不用源码目录或图节点推断 Module。

涉及：全部 Module 入口、Registry、Spec Context、Workflows、Publication。

### D02：每个 Module 都有实体关系图是项目约定

问题：原先“所有模块都需要 overview”和“简单模块可以省略”的约定混在一起，而且绑定展示 recipe。

决定：Concorde 自身所有 Module 都必须有主要实体及有向关系图，包括叶子 Module。图说明真实概念、
职责和边界；不为凑节点制造子模块。复杂行为可以另外保留状态图。这个约定不修改独立 Protocol
对绘图工具和简单 Module 的规定，也不把项目的英文约定强加给所有 consumer 项目。

涉及：根 Module、各 Module 的 Architecture、Constitution、Publication。

### D03：保留空的兼容字段，不重复装载同一图

问题：旧 snapshot/result 使用 `diagram_sources`、`diagrams` 传递外部 JSON。

决定：本次使用的 registry `diagrams` 为 `[]`；内嵌图随 Markdown 进入 `target_spec/shared_specs`，
不会再次放入 `diagram_sources`。作者通过 `documents` 返回含图的完整 Markdown；单独的 `diagrams`
结果省略或为空。图修改通过文档摘要使上下文、评审和发布证据失效。

旧外部源必须显式迁移，新的发布/作者契约不允许忽略旧声明后假装成功。保留 Profile 9 和 registry
schema 2 的字段形状；这不表示旧外部图无需迁移即可兼容。将来若需要独立 `.mmd` 源，须另行定义
明确的格式和身份约定，本次不引入。

实现待跟进：Registry/context/authoring 的旧 JSON 分支和对应错误行为。

### D04：修复图发布和导航的矛盾

问题：配套 Spec 同时声称 overview 放在文章之前、之后或 Architecture 内；导航也同时声称以
目录和 Module 树作为唯一主视图。

决定：Mermaid 在 Markdown 的作者位置渲染，不再注入独立 overview，不输出独立图 HTML 或图 receipt。
主导航按显式注册的文档路径分组；另有 Module 结构和 Implementation 列表视图。每个物理文档只有
一个 canonical page，显式共享文档保留全部成员身份，既有文档 alias redirect 承诺继续成立。
旧独立图 HTML URL 不在本次兼容承诺中；迁移后的引用指向所属 Markdown 的 Architecture anchor。

实现待跟进：独立图渲染/复制步骤、旧注入组件、scaffold 和部署模板中的 renderer 安装步骤。
Mermaid 语法错误或渲染失败必须阻止发布，而不能静默丢图；当前整站管线对此尚未验证。

### D05：把重复概述拆成真正的契约

问题：多个 feature、interface、Architecture 使用相同模板段落；段落标题存在不代表语义完整。

决定：每个 feature 分别描述触发条件、结果、限制和失败。Architecture 描述内部实体、关系、状态和
完成条件；interface 入口连接本 Module 已注册的完整接口文档。根 Module 明确七个开发者入口、
只读查询、候选 ready、交付与清理的不同完成条件。

涉及：14 个 Module 入口。保留原有身份，不通过改名字掩盖原来缺失的行为描述。

### D06：补齐直接依赖，区分调用方与提供方

问题：Reader factory 明确使用 Package Assets 和 Agent Execution，但 Spec Context 的 `uses`
未登记它们。File Transactions 使用 Registry 的字节/摘要读取和 Wire Contracts 的安全路径能力，
也未登记。Permissions 则把执行调用方的前置责任写成自己必需的反向 provider。

决定：补上 Spec Context → Package Assets、Agent Execution，以及 File Transactions → Registry、
Wire Contracts 四条直接依赖，并写入本地责任、使用条件和 relied-upon promises。
Permissions 的委派授权和执行回执检查明确为调用方责任，不引入反向依赖。
Agent Execution 中的 reader factory 标为调用方组合示例，不使 execution 反向依赖 context。
所有这些 Module 仍是根 Module 下的兄弟；没有增加结构父节点或转移文件所有权。

### D07：本地配套文档不冒充“共享 Spec”

问题：多个不同物理文件都自称同一 Shared Spec；Spec Context 的 runtime values 还引用其未注册的
Agents and Harnesses 文档，无法在自身集合中得到完整模型。

决定：保留现有独立物理文件和身份，明确它们是本地 companion documents；补齐 Spec Context 的
本地 Agents and Harnesses 并注册。给 Context/Workflows 的本地 registry values 补齐其承诺提供的
配置和版本解释，并在 Package Assets 内补齐 BuildResult、SkillPrompt、AgentBinding 等返回值定义。暂不合并为跨 Module 共享文件，避免在这次修订中顺带改变既有身份。

保留的取舍：本地重复内容以后仍需保持兼容。若要去重，应显式迁移 document identity/membership，
不能仅靠 hyperlink 把某个副本当作所有 Module 的共同权威。

### D08：明确完整查询域与现有 Module 执行入口的区别

问题：Protocol 的语义查询域包含 Module、Feature、Interface、Implementation，但现有
`select(target_id, focus_id)` 和 `resolve_context` 只描述 Module 执行入口。

决定：保留现有入口，另在 Registry Spec 定义只读 `spec_files(entity_id)` 和
`spec_pair(module_id, implementation_id)`。前者按显式身份返回完整文件集合；后者仅为明确关联的
Module/Implementation 返回两部分集合。二者不读取绑定源码，不授权 worker，不改变 Module 上下文。

实现待跟进：这两个接口是 Spec 新增设计，尚未写入代码。不能因为已写入 Spec 就宣称 Framework
已具备完整 Protocol 查询支持。若未来选用别的接口名，必须保持这里已确定的查询语义。

### D09：Implementation Spec 不再只写“遵守公共契约”

问题：实现文档已有精确文件清单，但接口、依赖、约束和验证部分大量重复同一段通用模板。

决定：18 个 Implementation Spec 分别写明具体实现入口、数据/控制职责、协作依赖、需保持的不变量
和有意义的验证场景。保留全部精确文件绑定；表中的 source family 只是解释分组，不能隐式拥有新文件。
Agent 的源码归 `implementation.agent-definitions`，并不因为被某个 Module 启动就转移所有权。

历史夹具中的 JSON 图和旧 Spec 是测试输入，仍属于其现有 Implementation owner；不是本项目的 live
Module Spec。它们的删除或转换留给代码迁移，不能先删绑定后假装这些文件已退出实现。

### D10：修复 review 默认值和生命周期表述

问题：配套文档一处写 `run_reviews` 默认 false，另一处写默认 true；开发状态图也容易被理解为
ready 后自动 delivery。

决定：默认 true；显式 false 记录 skip，并且不能取消既有 required review。开发以 ready 结束；
交付必须另行授权和调用。状态图补上这个边界及独立源声明。Reflection 的 `fast-loop` 路由标签
仍作为其现有字段值保留，不据此推断所有 dev-loop 的默认选项。

### D11：文件事务的恢复边界必须诚实

问题：“失败一定恢复全部状态”忽略恢复 I/O 本身失败、并发写入、文件模式、残留父目录等情况；
原接口也未说明 verifier 的 false 返回值并不表示失败。

决定：写清 `{path,before_digest,content}`、非空唯一变更集、成功路径顺序、错误分类以及
`verify()` 必须 raise 才能拒绝。调用方需独占被修改路径；本接口不承诺进程崩溃恢复、模式保持
或通用并发隔离。恢复失败必须显式失败，不能返回 applied；重试前读取实际状态并更新 preconditions。
所有直接消费者的 relied-upon recovery promises 一并调整。

这是明确现有接口边界，不在本次扩大为一个具备持久化 journal 的新事务系统。

### D12：Managed Runtime 的保存旧环境承诺尚未实现

问题：既有 Spec 承诺失败保留旧 runtime，但 direct `provision_runtime` 的 rebuild 分支会先删除
现有环境，失败后只清理新建的部分。调用方不能把未返回成功结果解释为旧环境已恢复。

决定：保留“新环境验证完成前保留旧环境，失败恢复旧环境”的产品契约；在本地接口明确标为
实现差距，不把当前破坏性顺序改写成推荐行为。补齐 RuntimeSpec、ViewerSpec、plan action、receipt、
健康检查及重试语义；`unchanged` 仍可能刷新 marker，并非只读操作。

实现待跟进：受验证的替换环境、恢复路径及失败测试。替换目录/切换的具体算法留在 Implementation
层选择；本次没有实现或验证该迁移。

### D13：修复上下文和反馈记录的局部不一致

问题：Snapshot 文档同时声称固定两个 Protocol records，又说 code writing 加入 Implementation kind；
record-gaps 的特殊输入与“所有 mutation 必须非空 reflection_ids”冲突；报告 provenance 把
注册列表第一项当作 Module 入口。

决定：普通阶段 principles + Module kind，code writing 再加入 Implementation kind；
record-gaps 使用非空 gap_ids 和空 reflection_ids；concerns 的 Module 入口来自唯一 module.md，
不依赖数组位置。修正本地协议/schema 名称、重复词和错误的 Module 文件归属说明。

实现待跟进：record-gaps provenance 是否已使用 primary_document 需在后续代码阶段核实；本次未运行
生命周期或反射系统操作。

## Archify 完整退出实现时的剩余范围

下列项目不是新的 Reflection，也不表示本次已修改它们：

- `prompts/protocol/framework-profile.md`、`agents/spec_author/spec.md` 及由它们生成的作者/规则资产：
  仍有旧 authoring recipe。修改应在 authored source 完成，然后在所属 worktree rebuild。
- `src/concorde/specification/validation.py`、初始化及外部源相关 reader/context 分支：移除旧 JSON
  硬约束，使作者、注册、上下文和本次 Markdown 契约一致。
- `docsite/scripts/render-diagrams.ts`、旧 diagram 插件/组件、scaffold/deploy 入口、对应 README：
  删除对独立 renderer/HTML delivery 的依赖，保留 Markdown Mermaid 发布。
- `src/concorde/autodocs/docsite_scaffold.py`、旧 understanding diagnostic 分支和相应测试：
  区分退出支持的旧输入与仍有价值的兼容/负例夹具，逐一移除依赖，不能以删除测试替代迁移。
- `skills-lock.json`、项目本地 archify Skill 安装和安装步骤：待实际使用点迁移后清理。生成资产不直接编辑。
- `README.md`、`docsite/README.md` 中旧指引以及未转换的 fixture assets：与实现迁移同步收尾。
- 更新 Framework profile 会影响生成规则和 `protocol/manifest.json` 的导出摘要。独立 Protocol 的
  内容版本不应仅因 Framework 选用 Mermaid 而改变；但包的精确摘要与 project binding 必须显式一致。

## 本次检查记录与未作出的结论

按用户要求，没有运行 Concorde validate、配置的代码检查、Spec/code review、build 或 build --check，
没有生成 ready/delivery 证据，没有提交或合并。开始时仅完成源 checkout 所需的 worktree affinity 确认。

做了修改自身的基本编辑核对：文档 JSON、身份/成员关系、feature/interface 定义位置、直接依赖集合、
Implementation 文件清单和 registry 一致，当前无发现的结构不一致。当前 live `specs/` 已无外部 JSON 图。

使用项目已安装的 Mermaid 和本地 Chromium 对 16 个 fence 做独立解析和 SVG 渲染，最终全部成功。
过程中修复了三个图把保留字 `graph` 当作 node ID 的语法问题。第一次纯 Node 尝试缺少浏览器 DOM，
不是有效的 Mermaid 成功检查；最终结果来自浏览器环境。未运行整站构建或宣称发布管线已迁移完成。

这些检查只支持上述有限结论，不证明全部语义完备，也不证明新 Spec 的行为已经由实现满足。

## 剩余修改提交前的补充审阅

在用户要求检查并提交其余工作区修改后，将独立 Protocol 章节与模板、include resolver、包摘要绑定、
站点 Protocol 导航/Mermaid 依赖、旧 Spec 文件删除及相关测试作为同一组关联修改提交。
修正 README 指向已改名章节的链接，并把当前仓库的 production-build 断言从旧 iframe/旧标题
改为现有页面入口与不再嵌入外部图的结果。

确认尚未完成的实现对齐：

- Framework profile、Spec author/reviewer、初始化器及历史发布分支仍保留旧外部图约定；这些源文件
  的现存改动随本次提交保存，并不表示已完成 D01–D04 所述的运行时迁移。
- 当前 scopedSidebar 已改成 Module/Implementation 两套导航，尚未实现 D04 保留的文档路径主视图。
- 当前 Page.title 使用 Module 标题或文件名，和 publication/pipeline.md 中仍保留的 H1 优先段落
  不一致。后续应明确区分正文标题与导航标签，并统一其返回值契约。
- 所安装的 Mermaid theme 在客户端完成渲染；静态站点构建成功不能证明浏览器中每个图均成功渲染，
  也不等于已经实现“Mermaid 错误阻止发布”的新承诺。

这些差距继续在本文件跟踪；本次提交保存已有工作，不把它们改写成已完成的迁移。

补充验证结果：Prompt resolver/build 的 48 项 Python 测试通过；scoped registry/site identity 的
40 项测试通过；包含实际整站构建的 production-build/framework-guides 7 项测试通过，共 95 项。
`git diff --check` 通过。没有运行 Concorde 的完整验证或评审流程，也没有据此声明所有新契约已实现。

## 交付流程修改提交前的补充审阅

这批工作区修改把默认 delivery 改为发布 `concorde/delivered/<change_id>` 并清理源 worktree；
主分支只由主 worktree 会话的独立 `merge_primary:true` 请求更新。显式保留、脏主目录保护、
共享仓库锁、分阶段检查日志和可恢复回执随接口、指令、Spec、导出摘要一起更新。

本次审阅补上两个实际问题：

- 初次交付或清理重试中断时，`keep_worktree:true` 可能尚未写入回执，导致下一次未带该参数的
  重试删除本来要求保留的 worktree。现在先持久化保留选择，再发布分支或尝试清理；显式 false
  仍可解除保留。两个真实 Git 回归场景先复现失败，再验证修复。
- 旧 schema-1 直接合并回执的重试提示错误地声称“主分支未变化”。现在按回执是否属于新分阶段
  交付区分提示，保留旧记录的真实目标和清理重试行为，并增加兼容性回归测试。

开发状态图也明确区分 Delivered 和 PrimaryMerged。检查使用项目 `.venv`：交付/生命周期/
worktree 边界相关 63 项测试及构建/类型/能力声明 45 项测试通过；最后另跑 4 项针对性回归，
包含新增的旧回执场景，全部通过，共覆盖 109 个不同测试。系统 Python 缺少 langgraph 的初次
运行不作为代码失败结论。源码投影已 rebuild，`git diff --check` 通过；没有执行项目的完整
Concorde 验证或 Agent 评审流程。

## 重组：按能力划分的六个 Module 与 Harness

日期：2026-09-09。规范依据：Spec Protocol 2.1.0。本节记录根 Module 重组的直接维护决定。
决定已写入注册表、`specs/`、`protocol/` 与 Framework profile；标为“实现待跟进”的条目表示代码尚未
对齐新契约。

### D14：十三个兄弟 Module 收成六个按能力划分的 Module

问题：原十三个子 Module 按代码层次划分。Harness 概念被切在 Workflows、Agent Execution、
Permissions、Spec Context 和 Package Assets 五处；四个 Module 各持一份逐字节相同的
Agents and Harnesses 与 runtime-values 副本，三个 Module 各持一份相同的 registry values；
Wire Contracts 与 File Transactions 是实现基础设施却因“共享 provider 必须与消费者是兄弟”的规则
被迫成为顶层 Module。

决定：根 Module 下只保留 Spec、Harness、Development、Reflections、Distribution、Views 六个
Module。Spec 拥有 Protocol 绑定、注册表、结构校验、初始化与按 ID 解析文件集；Harness 拥有四种
context 的冻结、Agent 与 Harness 定义、权限编译、原生执行与 LangGraph 控制流；Development 拥有
提问、开发循环、拓扑、候选证据与交付；Reflections 不变；Distribution 拥有构建、安装、配置与受管
运行时，Build 从功能上属于它，Harness uses Distribution 获取渲染后的指令与新鲜度；Views 拥有文档站
与代码图查看器。Wire Contracts 与 File Transactions 降级为 `implementation.typed-values` 与
`implementation.file-transactions`，由需要它们的 Module 引用。重复副本各保留一份，归 Harness 或 Spec。
Reflections 与 Development 互相 uses；uses 关系不构成需要拆分的环，只有 parent 必须无环。

### D15：Protocol 2.1.0 定义 implementation context

问题：代码里“写代码阶段拿到的实现知识”由 Module 的 implementation 引用唯一确定，但 Protocol
只定义了 Implementation Spec 自身的 Context(R) 与显式配对 Context(M, R)，并把绑定文件写成
“执行请求可另行授权的扩展”；spec-and-context.md 的图还把 Context(R) 的节点称作 Implementation context。

决定：Protocol 升到 2.1.0。Spec and Context 新增 Implementation context 一节，定义
`ImplementationContext(M) = ⋃ (D(R) ∪ A(R) ∪ F(R))`，Feature 与 Interface 沿用其 providing Module
的结果；它与 Context(M) 不相交，共享 Implementation Spec 不带入其他使用者的契约，工具只能按阶段
取子集而不能扩大。原节点改名为 Implementation Spec context；P2 点名该术语；模板与 README 同步。
manifest 与 `.concorde/config.json` 重新绑定到新摘要。

### D16：Framework profile 记录四种 context、LangGraph 与 Mermaid 约定

决定：P5 把一次调用冻结的 context 明确为 Spec context、implementation context、capability context
与 task context 四种，某一种可以为空但闭包非空；Agent 指令、Protocol 规则包与 Skills 不是 context，
Skill 只是 global 或 lifecycle capability 装进开发者 workspace 的投影。P7 规定每个 capability 的
控制流都是 LangGraph 图，节点是不调用模型的确定性步骤或调用模型的 Agent，leaf 可以是任一种，
Studio 展示的就是这些图。作者约定改为内嵌 Mermaid，删除已退出的 Archify 与 `generated/diagrams/` 描述。

### D17：确定性 capability 与 model-backed capability

决定：Agents and Harnesses 把 capability 分成不发起 model 调用的确定性 capability 和至少调用一次
model 的 model-backed capability，后者即 Agent。这个区分描述模型是否参与，不描述输出是否可复现。
leaf 可以是纯 Python 步骤或一次模型调用；原“Python 控制逻辑实现的 Agent”提法删除。Harness 不再
admit Skills；Agent 可用的 Capability 与 Tool 契约构成 capability context。

实现待跟进：`Harness.skills` 字段仍在记录形状中且全部为空，删除会改变所有 Harness 摘要与 Agent 绑定；
snapshot 尚无 capability context 字段。

### D18：统一命名

决定：Module ID 为 `module.<name>`，title 与根图标签等于 name；feature 为
`feature.<module>.<verb>`，interface 为 `interface.<module>.<name>`，不再使用 `api.` 前缀；
document 为 `document.<module>.<basename>`，Implementation 文档为 `document.implementation.<name>`；
check 为 `check.<module>.<name>`。文件夹树按新 Module 树重排，一个 Module 一个文件夹。历史 delivery
证据中的旧 ID 属于归档，不改。四条待处理 Reflection 原先归属于注册表中不存在的
`feature.concorde.evolve-protocol`，按其内容改归 Development、Harness、Spec 和 Harness。

### D19：relied_upon_promises 改写为消费者视角

问题：原依赖块逐字复制提供方接口全文，Wire Contracts 的同一段出现在九个文件里。

决定：保留 Protocol 的必填字段，每条只写消费者自己依赖的一两句承诺，不复制提供方接口原文。
根 Module 的六条子 Module 条目按此重写。

### D20：Implementation Spec 按变化原因重组

决定：`spec-engine` 拆为 `spec-model`（注册表、校验、初始化、`concorde-init`、包入口）、
`context`（上下文解析）与 `legacy-understanding`（Profile 7 遗留代码、fixture 与测试，显式标记待删除，
并列出四处活引用：CLI `validate` 子命令与 reflections_queue 脚本调用旧校验器，reflection 校验与
docsite 脚手架使用旧仓库类）。`workflow-host` 拆为 `development-host`、`agent-model`（Agent、
Harness、effects 与 roles 投影）和 `studio`。`workflow-capabilities` 按能力归属拆到 Development、
Spec、Distribution 与 Reflections 的实现，Skill 源与 prompt 片段随其能力归属。`package-build` 改名
`build`，`wire-contracts` 改名 `typed-values` 并纳入 frontmatter 解析器。共 21 个 Implementation Spec，
每个文件仍只有一个 owner，绑定清单由注册表生成。

实现待跟进：`capability_host.py` 仍包含 Harness 规定的绑定与启动机制，需要抽到 Harness 的实现；
main 的 discovery 循环、递归 AgentRuntime、reflections-triage、topology 与四个 lifecycle capability
仍是普通 Python 控制流，需要改成 StateGraph 并让 `generated/langgraph.json` 指向真实图；遗留包及
其 fixture 与测试的删除和四处引用迁移；`initialize.py` 仍写旧的外部 JSON 图；`model.py` 仍保留
Profile 7 实体类；`spec_files` 与 `spec_pair` 尚未实现；文档站需要为移动后的文档声明旧 URL alias；
`generated/roles` 与 `generated/diagrams` 是构建不再产生的残留输出，待清理。

### 重组的检查记录

`python3 scripts/concorde.py build` 与 `build --check` 通过；`protocol-manifest --write --bind-project`
把 `.concorde/config.json` 绑定到 Protocol 2.1.0 的新摘要。`validate_repository` 与 `validate_package`
均无 finding。用本地 Playwright Chromium 加 Mermaid 11 解析并渲染全部注册 Markdown 的 9 个 fence，
全部成功；四个新图曾把保留字 `graph` 用作节点 ID，已改名。

Python 全量测试 722 项，8 项跳过，3 项失败；这 3 项在 HEAD 的独立 worktree 上用 HEAD 自己的源码
复现出完全相同的失败，属于本次之前已存在的问题：fresh-clone bootstrap 的两项把
`service.workflow-host` 当作自托管 target，该 ID 在 HEAD 注册表里也不存在，已改为 `module.development`，
但该测试克隆的是已提交的 HEAD，因此要到本次修改提交后才能通过；Studio 的
`test_source_studio_delivery_retains_its_worktree` 期望交付保留源 worktree，与上一次提交把默认交付改为
删除源 worktree 的行为冲突，本次未改动交付语义，留给交付的维护者决定。

docsite 安装依赖后 `tsc --noEmit` 通过；framework-guides、scoped-registry、diagram-inventory、
feature-graph、github-pages 与 production-build 共 44 项通过，其中 production-build 原先硬编码
`module.workflows`，已改为 `module.development`。整站构建从新的六 Module 结构成功生成关系图与页面。
未运行 Concorde 的 dev-loop、Spec/code review 或交付流程；没有提交。

## 源 checkout 的 worktree 守卫

日期：2026-09-09。本节记录用运行时拦截取代 `verify-worktree` 的直接维护决定，只涉及 Concorde 自身的
源 checkout，不改变 Protocol，也不装进使用 Framework 的项目。

### D21：禁止开发者会话自行创建 worktree，取代 verify-worktree

问题：`verify-worktree` 要求每个 agent 会话在开工前、以及每次 cwd 变化后，拿运行时通告的绝对
Skill 路径手工跑一次校验，并据结果自行发起 P10 交接。这一套依赖 agent 记得执行，流程复杂。
真正需要保护的只有开发者自己的主会话（Claude Code、Codex CLI）和它自行创建的原生子 agent：
主会话在 worktree A 加载 Skills v1，子 agent 创建或进入 worktree B，却仍带着 v1 的指令。Concorde
自己的 worker 由 Python host 在正确目录启动，从不存在这个问题。

决定：开发者会话不得自行创建、移动或进入 worktree；worktree 只由 Concorde host 创建（调用
`concorde-dev-loop` 等 capability），随后按 P10 在新 worktree 里开启新会话。这条规则由 agent 运行时
强制执行，不再依赖 agent 记忆：`.claude/settings.json` 的 deny 规则拒绝 `EnterWorktree`、
`Agent(isolation:worktree)`、`git worktree add|move` 和 `claude --worktree` 前缀，`PreToolUse` 与
`WorktreeCreate` 钩子运行 `scripts/worktree-guard.py`，后者覆盖前缀规则表达不了的写法（`git -C`、
`sh -c` 包装等），并让 `claude --worktree` 在启动时就失败；`.codex/rules/worktree.rules` 以 execpolicy
`forbidden` 拒绝 `git worktree add|move`，`.codex/hooks.json` 在每条 shell 命令前运行同一守卫。
守卫脚本只用标准库，只读 stdin 的钩子载荷，拒绝时输出 `permissionDecision: deny` 与原因并以 2 退出，
输入不可读时以 1 退出（可见但不阻塞）。它是守护而非沙箱：运行时拼出的命令和已运行 shell 的 stdin
不在其覆盖范围；整段命令文本都会被检查，因此需要提及这些命令的文件用编辑工具而不是 shell heredoc
写入。Codex 只在项目受信任时加载项目 `.codex/` 层，项目钩子还需用 `/hooks` 审核一次，审核前由
execpolicy 规则兜底；两个运行时都把规则和钩子同样施加于原生子 agent。

边界：这是开发 Concorde 仓库自身的策略。安装器不分发守卫脚本和这三个集成文件，消费者项目不会得到
任何钩子。Concorde 自己的 worker 不受影响：Claude worker 以 `--restricted` 启动，忽略项目设置；
Codex worker 以 `--ignore-user-config` 启动，项目 `.codex/` 层因此不受信任而不加载。

随之删除：`verify-worktree` 子命令、`src/concorde/host/worktree_affinity.py` 及其测试；`AGENTS.md`
的“Worktree affinity”一节改为“Worktree ownership”；`CLAUDE.md`、README、STUDIO.md 与 Distribution 的
Module Spec、`implementation.installation`、`implementation.worktree-lifecycle` 同步改写；守卫脚本与其
测试绑定到 `implementation.installation`（安装器已列出脚本清单，且注册表禁止绑定 `.claude/`、`.codex/`
下的文件，三个集成文件与 `AGENTS.md` 一样是 checkout 的集成配置）；原随 affinity 测试文件存放的
候选 worktree 自建构建测试移到 `tests/concorde/host/unit/test_change_worktree.py`。与既有 Spec 无冲突：
P7 只说明白授权的维护会话可以直接改项目，P10 的交接不变，host 创建 worktree 的路径不变。

技术依据（2026-09-09 核对官方文档并在本机 Claude Code 2.1.266、Codex 0.153.4 上实测）：Claude Code
的 `WorktreeCreate` 钩子非零退出即中止 `--worktree`、`isolation: "worktree"` 与后台会话的 worktree
创建；`PreToolUse` 钩子与 deny 规则同样作用于子 agent；`${CLAUDE_PROJECT_DIR}` 指向会话起始的项目根。
Codex 0.153.4 没有原生 worktree 功能（`main` 分支上有尚未发布、默认关闭的实验特性 `worktrees`，
届时可在项目配置里关闭），子 agent 与父会话共用 cwd；项目级 `.codex/hooks.json` 与 `.codex/rules/`
在受信任项目中加载。

### 守卫的检查记录

`python3 scripts/concorde.py build --check` 与 `validate` 均通过（注册表绑定含新增与移除的文件）。
守卫、候选 worktree、handoff、worktree 边界与生命周期、Distribution 结构共 64 项定向测试通过；
`codex execpolicy check` 对规则文件给出 `forbidden`（`git worktree add|move`）且不匹配 `git worktree list`。
Python 全量测试 734 项，8 项跳过，2 项失败：fresh-clone bootstrap 克隆的是已提交的 HEAD，其中还没有
守卫脚本，提交后重跑通过；Studio 的 `test_source_studio_delivery_retains_its_worktree` 是上一节已记录的
既有失败，本次未触及交付语义。docsite `validate` 与 150 项测试通过。

在本 checkout 里用子会话实测：Claude Code 对 `sh -c 'git worktree add …'`（只有钩子能拦）、
`isolation: "worktree"` 的 Agent 调用均在执行前拒绝并回显原因，`claude -p --worktree` 因
`WorktreeCreate` 钩子失败而退出码 1，未生成任何 worktree；Codex 对直接的 `git worktree add` 与
`sh -c` 包装形式均由 `PreToolUse` 钩子拦截（实测使用 `--dangerously-bypass-hook-trust` 代替尚未做的
`/hooks` 审核）。本次按用户授权直接在 main 上提交，未 push；未运行 Concorde 的 dev-loop、Spec/code
review 或交付流程。
