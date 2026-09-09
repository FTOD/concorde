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
