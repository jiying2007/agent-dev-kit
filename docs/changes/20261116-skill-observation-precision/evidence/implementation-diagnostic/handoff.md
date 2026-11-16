# T1 / T3 实施交接

实施者：diagnostic_methods。当前工作树基线 `fad9d4d170a97c5dbb2c5261432fa2120bfcc3c9`；未提交、推送或执行全量回归。生产写入已停止，交 parent 冻结源码和执行后续消费者、独立审核及精确远端 SHA 全量验证。

## 已落地

- `skills/adk-fault-injection-recovery/SKILL.md`：1.0.4 / 2026-11-16；加入同输入无故障对照、实际命中、未知命中和独立检测/恢复检查。发布的短 Python 示意只返回 `not_evaluated` 或“待核检测与恢复”，不返回整体 pass，不判 SLA/设备资格。保留原隔离授权、独立操作者、预算、恢复命令、回滚、停止、真实回执、数据/功能及条件性 watchdog 约束。
- `tests/test_skill_fault_activation.py`：6 个定向测试，提取发布示意并使用实际 host GCC/GNU ld C 夹具校准；命中证据隐藏时 JSON 实际输出 null，错误返回和健康 follow-up 仍不能反推命中。
- `tests/fixtures/fault-activation.c`：有界自身进程分配故障；正常、未触发、触发、证据不可用和故障路径错误清理。原审计探针没有修改。
- `tests/test_skill_content.sh`：仅在原聚合入口增加 `tests.test_skill_fault_activation` 和 task_data 实施的 `tests.test_skill_imap_time_methods`，各一次；不增加 Gate 或 suite。
- 现有 `scripts/version-manager.sh upgrade --target 11.3.12 --force` 同步 `manifest.json`、`.version-lock`、`pyproject.toml`、`src/agent_dev_kit/__init__.py`、`README.md`、`CONTEXT.md`、`manifests/software_m5_eval_contract.json`。既有 `catalog build` 执行成功，没有产生目录正文差异。
- 收到 task_data “写集已冻结”交接后，串行把 `optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md` 元数据前移到 1.0.4 / 2026-11-16。逆向只还原这两行后 hash 等于其冻结值，未改正文。
- `tests/fixtures/skill_method_ab_prereg.json`：candidate 仅前移到 v11.3.12，并保留 v11.3.11 / fad9d4d1 的未执行身份。原 train/holdout、判据、预算、results 和 no-model-runs 不变；精确结构比较与原测试均通过。

## 定向证据

| 收据 | 结果及范围 |
|---|---|
| `fault-method-red.json` | 旧入口缺少新发布观察示意，单项回归按预期失败；这是方法新增的红信号，不是声称旧运行态判定器有漏洞。 |
| `fault-method-green.json` | 6 项故障方法 + 原设备只读/操作者合同，7 tests PASS。 |
| `combined-methods.json` | 两个新模块共 13 项，加原设备合同，共 14 tests PASS；含真实 null 命中证据和错误清理对照。 |
| `version-upgrade.json` / `version-identity.json` | 既有版本同步入口及版本投影校验 PASS。 |
| `prereg-identity.json` | 原预注册条件/身份测试 PASS。 |
| `profile-ratchets.json` | 原测试逐项检查全部 8 Profile，PASS。 |
| `strict-validation.json` / `strict-final.json` | 既有 strict 校验；最后一次覆盖最终预注册身份及留存导出文件后的状态。 |
| `claude-export.json` | 现有 exporter 真正执行，claude-code + embedded-fullstack + 显式 optional adk-email-imap-fetch，PASS。 |
| `delivery-inspection.json` | 65 个 Skill 身份保持，manifest 除 version 无差异，原 Profile 阈值字节不变，8 Profile 通过，99 个实际导出文件的集合和摘要逐一一致。 |
| `aggregate-shell-syntax.json` / `diff-check.json` | 原聚合入口语法和 tracked diff 空白检查 PASS。 |

每个命令收据保存实际 argv/cwd、退出码、stdout/stderr、时长及当次关键源码摘要。这些时长只是本机验证过程耗时，不是方法效果或恢复 SLA。

## 字节与八个原预算

故障 Skill `3559 -> 3558 bytes`，净减 1 byte；没有挪减其他 Skill、增加 reference 或提高阈值。下表为实际潜在完整源字节 / 原限额，entry 字节也全部通过；不是模型 token 实测。

| Profile | 实际 / 原限额 |
|---|---:|
| core | 172867 / 184133 |
| embedded-fullstack | 316438 / 316854 |
| incident-response | 46451 / 46612 |
| large-refactor | 323320 / 323328 |
| personal-core | 191686 / 204293 |
| release-hardening | 156162 / 159576 |
| research-intake | 117004 / 124543 |
| team-core | 210852 / 223333 |

## 真实导出与消费者输入

完整实际导出在 `/workspace/scratch/2d4d08f07657/other-skills-export-11.3.12/claude-code`。仅两份原样 Skill 已留存到本证据目录下：

- `exported-consumer/adk-fault-injection-recovery/SKILL.md`
- `exported-consumer/adk-email-imap-fetch/SKILL.md`

该子目录没有诊断、预期答案或任务分析。父级可仅向独立消费者提供原始任务工件和对应真实导出；不要把本交接或测试答案作为消费者输入。

| Skill | 源 SHA256 | 实际导出 SHA256 |
|---|---|---|
| fault | cfffdf6b98594802f65acee8f0258ed44eff8d5bb5c2a02eca6f5df60567f209 | e2ca83b2a2f6f67d379214f00584358c78f579c8883832c08be483b79e651bba |
| IMAP | b109548aceb24d3f978e92eb4706cc0845847c82a741d05810ded49f44f351b7 | 09c31d595ff2aa073af02bcb3951ebf22a576b645e5f6b5164bed5326c8bb4d7 |

源与导出 hash 不同源于现有 target renderer 重写 native frontmatter；两个 Skill 的完整正文逐字一致。`adk-export-manifest.json` 留存真实 export manifest，具体源/导出路径、摘要和验证过程在 `delivery-inspection.json`，原 exporter 参数在 `claude-export.json`。

## 边界与负结果

- host C 与本地 IMAP 协议不等于硬件/HIL、恢复 SLA、真实邮箱一致性或模型/成本收益；本次没有设备写入、真实邮箱、外部发送、安装或付费模型调用。
- 原审计 C、runner 和 JSON 的 SHA256 均复核不变，见 `delivery-inspection.json:original_probe_preserved`。
- 初次读取辅助 CLI 时猜测了不存在的 `src/agent_dev_kit/commands/distribution.py`，该 rg 返回 2；随后按已存在的 CLI、model 和出口实际调用工作，未用错误查询推导结论。
- 初次在三个候选测试文件中搜索预注册 fixture 为零命中；随后全 tests 精确检索定位到 `test_skill_quality_methods.py`，实际执行对应旧测试通过。
- 最初精炼草稿为 3564 bytes，在首次绿色验证前通过合并同 Skill 重复说明改为 3558；未改预算。
- 完整回归、独立消费者/最终审核、受保护提交及发布均归 parent 后续处理；这里不声明它们已完成。
