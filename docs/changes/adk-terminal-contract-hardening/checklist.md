# 交付清单：adk-terminal-contract-hardening

- [x] 改前假绿/漂移均有可复现负证据。
- [x] 根性能包装器实际执行 strict timing budget。
- [x] quick 真实耗时满足现有预算且未删除测试或放宽预算；重型回归保留在 full/根包装层。
- [x] install manifest、schema、installer、CLI 和文档统一为 copy-only。
- [x] 关键 manifest object 有结构化 schema 与负向测试。
- [x] Python/依赖支持基线与 CI、文档一致。
- [x] 定向、quick/full、security、release 和根集成结果已记录。
- [x] breaking change、迁移和 rollback 已明确。
- [x] 外部 runtime、远程 CI 与 field blocker 未被本地 fixture 冒充关闭。
- [x] Python 3.11/3.12 本地容器 parity matrix 通过。
- [x] CI waiver 限定为 7 天、本地继续开发，并机械拒绝发布/认证解释。
- [x] PEP 639 license metadata 在隔离 build 中不再产生旧格式弃用告警。
- [x] RC3 source commit、可复现 artifact 与 rc.2 → rc.3 rehearsal 完成；根仓锁定由父仓证据提交承接。

## 治理模板保留项

- [x] Prompt before/after 对比证据
  - 本变更不改 prompt；以性能、schema、安装和支持环境行为 before/after 证据替代，reviewer 已复核。
- [x] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）
  - `verification-evidence.md` 已记录命令、退出码、摘要、路径、层级与关联工件。
- [x] Skill Intake 归属与安装范围结论
  - 未引入第三方 Skill；所有改动属于 ADK core 与根验证包装层，未写 live runtime。
- [x] 收敛结论或阻塞说明
  - 本地 source/test pass；真实 runtime、远程 CI、candidate rehearsal、独立仓、第二操作者和 30 天 field evidence 保持 blocker。
