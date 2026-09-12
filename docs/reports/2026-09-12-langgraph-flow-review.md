# LangGraph Flow 迁移复核

本次维护将 Flow 定义为 Concorde 对可执行 LangGraph `StateGraph` 的称呼。Spec 使用 Flow
描述编排，保留 LangGraph API 名称、稳定 Spec ID、旧 Python 导入别名和持久化的 `graph` 字段。

复核涉及 Development、Harness、Views 的相关契约，以及引用这些文档的 Concorde 和 Reflections
完整上下文。各上下文的文档归属、引用来源和字节摘要记录在
[复核证据](2026-09-12-langgraph-flow-evidence.json)。复核方式是本维护会话的语义检查与自动结构、回归检查。

已落实的控制边界：

- 能力准入、工作区绑定和 dispatch 使用同一套 Flow，供本地调用与 Studio 执行。
- discovery/query、拓扑 author/apply、planning、development loop 和 Reflection triage 使用显式节点与条件边。
- 多 Module 协调、批量 author/review、最终验证收敛和递归 Agent 决策使用有界 Flow。
- Python 保留节点内的数据校验、单次 Agent 调用和确定性操作；delivery 的原子事务保持在同一锁与回滚边界内。
- Studio 展开实际执行的子流程；Agent Flows 页面从相同工厂编译节点与边，保留入口、恢复和无代码绑定等变体。
- host 与回调保存在每次调用独立的 runtime context 中，流式更新及公共 checkpoint 保持 JSON。

复核确认，原有 task/context 身份、权限隔离、review 要求、唯一自动修复边、取消与调用限制、delivery 授权均继续适用。
新增场景覆盖执行与查看来源一致、无副作用检查、JSON 边界、并发隔离和超过默认调度步数的有界执行。
Spec 仍明确记录与本次迁移无关的 invocation-binding 实现归属待整理问题。

LangGraph 1.2.11 默认忽略禁用 checkpoint 的子流程自动发现。适配层将实际执行的子流程实例登记给
Studio/xray，并以展开查看、嵌套流式更新和 checkpoint 测试约束这一兼容性接点。

验证结果：

- 全量 Python 回归：719 项，8 项可选 Studio 测试跳过，其余通过。
- 最后补强调度异常封装与 review 指纹后，相关 Flow、Studio 和 review 回归 70 项全部通过。
- 启用实际 Studio 服务器后，原有 8 项集成测试全部通过；新增的 HTTP viewer 展开检查也通过。
- Spec 离线审计通过；Framework 结构验证成功、0 错误。全仓库保留 42 条其他覆盖声明告警，本次 Flow 场景无此类告警。
- 构建产物新鲜度检查、文档站 TypeScript 检查、Spec 链接测试及生产构建通过。

调度器自身的异常仍经原有错误封装和结束事件返回。抽出的 review 批处理 Flow 已纳入 review
输入指纹，修改其代码会使旧审查证据失效。改动与复核材料保留在本工作区。
