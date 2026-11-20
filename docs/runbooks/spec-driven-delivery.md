# Spec-driven delivery：基于现有 Canonical Change Contract

适用：跨模块、行为变化、接口迁移、状态机、通信协议；不适用：仅重命名/格式调整、已有明确验收的单点修复。**ADK 不新增 Spec 引擎、第二套 Workflow/路由/权限或 OpenSpec 兼容层。**

## 唯一规格事实源

已有项目若有权威规格，先引用它；当前 ADK 变更复用 `docs/changes/<id>/proposal.md` 下的 `## Canonical Change Contract`，固定 `REQ-NNN → ADDED/MODIFIED/REMOVED → affected surface → ACC-NNN → TASK-NNN → VERIFY-NNN`。必要时在现有 `design.md` 补示意状态/接口，不另复制一份独立真相。实际实现与验证分别由 Git 和可信原始测试回执证明。可追溯 `spec → code → test`，从变更的可观察行为反向核对规格；缺依据标 `not-checked`。

需求来源可来自飞书项目、TAPD、用户、现场缺陷和架构讨论；记录外部来源标识但不强制转 GitHub Issue。未正式批准的建议不得伪称 owner 决策。

## 三种真实工作路径

### A. 已确认需求的小修
读取影响代码、明确现存行为和断言；直接改最小实现并运行定向回归。没有行为变化或对外合同影响，**不**强制生成规格、架构图、任务包和多轮询问。发现更改 public API 才升级。

### B. 新功能/架构演进
1. 仅在关键选择未决时使用现有 `adk-structured-requirements-questioning`；给候选、反例和可证伪实验，区分 user-confirmed/AI-proposed。
2. `adk-requirements-triage` 把已知目标映射成 `REQ`、行为 delta 与正负 `ACC`；旧规格只记增删改，不重写全量。
3. `adk-interface-contract-design` 明确 caller/owner、状态机、资源、异常、超时、兼容和回滚。
4. `adk-task-breakdown` 先选一个可关闭的纵向 slice，关联 `TASK/VERIFY`；实际实施沿用 `feature-delivery`。
5. 使用 `references/spec-code-bidirectional.md` 双向核验。任何 `contradicted/absent/not-checked` 必须报告，不能被标为 PASS。

### C. SoC ↔ MCU UART 双仓协作
- 协议只有一个权威版本化文档/哈希：帧格式、长度、大小端、校验、序列号、错误码、握手/重连、超时/重试及能力协商；每个仓保存引用与目标身份，不维护镜像。
- SoC 发送端与 MCU 接收端各有契约测试；至少覆盖正常、损坏帧、乱序/重复、超时与断电恢复。
- 设备不可用时 `not-tested`，不能由一侧 CI 推断双端系统已经联调成功。共有协议更新由单一 writer 负责；两侧独立实现最后进行集成验证。

## 失败与退出

缺少验收反例、协议来源、必要调用端或真实测试证据时报告 UNKNOWN/needs-fix；无新信息不重复访谈或启动 Goal。中高风险保持授权与恢复门禁。任务完成不等于模型效果改善；对 Skill 改进的增益应走 `docs/evals/interactive-discovery-evaluation.md` 的真实 A/B，源码测试只算 E0/E1；没有真实模型和受信 Host 时，E2–E4、Token/费用及行为收益均为 `not-measured`。
