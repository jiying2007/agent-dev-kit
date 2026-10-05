# 任务与检查点

- [x] A：隔离回归 fixture；root rollover / ADK bundle 定向通过，正式发布 clean-source gate 保留。
- [x] B：关键 manifest/contract/receipt、JSONL task/effect 输入统一严格解析与限额；额外 NaN/Infinity/溢出/深度负例通过。
- [x] C1：21 个固定工具副作用与 MCP 演练；不执行外部动作。
- [x] C2：transport、audience、redirect/private destination、caller/handle 负例接入 canonical CLI。
- [x] D1：intake 文件事务、reference 生命周期契约与 removal 规划分别归属 typed 模块；原消费者端口保留。
- [x] D2：官方来源 checker 拆为 6 个只读阶段；独立 AST 审查确认 322 条业务语句保持一致。
- [x] D3：Provider/Execution Policy 文档入口收敛；report retention 默认只读且缺依赖覆盖 fail-closed。
- [x] E：12 个任务、3 trial、72 次计划运行；用户选择仅落地工具，不调用模型。
- [ ] F：定向/全回归/最终快照矩阵、fresh review、候选归档与 final gate。

状态：源码实现已完成，最终快照验证待回读；逻辑任务仍开启；预算获用户授权上调至 3000 万；模型调用明确不执行。

复审修正：独立 review round 1 提出 1 major（JSONL task 非有限/深度未统一）、1 minor（retention symlink/相对引用/遍历限额）。两项已有实际消费者负例，修正后冻结新快照并进行复审。最终矩阵和权限结论以根仓 docs/changes/20261005-internal-external-iteration.md 的 Phase F 记录为准；本清单不自证发布资格。
