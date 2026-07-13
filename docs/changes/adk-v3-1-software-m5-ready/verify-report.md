# 验证报告：adk-v3-1-software-m5-ready

## 当前状态

- 阶段：实现、阻塞级审查修复、完整回归、可复现构建和本地升级演练完成。
- 产品声明：`M5-ready release candidate`，不是 `M5 certified`。
- 外部阻塞：Claude CLI 已安装但未认证，因此完整双 runtime campaign 未执行。

## 已通过定向门禁

| Gate | Result |
|---|---|
| strict / security / release check | pass / pass / pass |
| 60-task deterministic routing | 60/60，P95 `0.330ms` |
| matcher effectiveness | 25/25 |
| fallback sunset matrix | 14/14 rows |
| software M5-ready contract | pass |
| product maturity v3 transaction/release contract | pass |
| quick regression | 15/15，`113029ms` |
| full regression | 49/49，`293441ms` |
| source archive reproducibility | 两次独立构建 SHA256 一致 |
| wheel isolated install | `pip check`、非仓库 cwd `adk --help`、版本校验通过 |
| local release rehearsal | `3.0.0 -> 3.1.0-rc.1 -> rollback`，31 项资产恢复 |
| root software M5 certifier | synthetic positive/negative 与 live `m5-ready + blocked` 均通过 |

full suite 中超过 30 秒的测试为 `test_workflow`（`31356ms`）、`test_integration`
（`41950ms`）和 `test_performance_ops`（`58639ms`），三项均通过。

## 最终验收待填

- 提交与远端 commit 核验。

## 评审结论

- blocker：0 个未闭环。
- major：0 个未闭环。
- 已补强：writer lock 主机/PID/stale 判定、receipt/backup digest、双故障恢复、
  archive 路径/成员/大小边界、runtime timeout、campaign 合同类型与预算边界、原始结果证据。
- 保留阻塞不属于软件缺陷：Claude 未认证、30 天独立 pilot、第二位人工操作员和独立评审尚未发生。

## 边界

- 不用 synthetic runtime 代替 Claude 真实 campaign。
- 不在 eligibility 前创建 final `3.1.0`、tag 或 remote release。
- 生成型 release/runtime evidence 不进入 source distribution，避免 artifact SHA 自引用。
