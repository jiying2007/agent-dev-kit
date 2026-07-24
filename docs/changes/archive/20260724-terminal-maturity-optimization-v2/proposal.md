# 变更提案：terminal-maturity-optimization-v2

## 背景
- 2026-07-23 全面成熟度审计确认：ADK 当前工作区 full 56/56、Python
  3.11/3.12 quick parity 通过，但根仓 full 仅 52/58，根测试逐项补跑仅
  13/15。
- 根 `check-all.sh` 不覆盖全部 `tests/test_*.sh`，失败时默认删除子检查
  输出；`test_architecture_reports.sh` 的正向 fixture 已与 checker 合同漂移。
- 宿主 `python3=3.8.10` 时 ADK tests 可运行而 doctor 明确不支持，稳定入口
  缺少统一、可操作的解释器选择与支持状态提示。
- scorecard 同时出现 `level=M4`、`evidence_level=M3`、`status=verified`
  和未闭环 gap，容易把实现成熟度误读为证据成熟度。
- strict ADK dirty 与三个过期 observe baseline 使 current-status、
  evidence-bundle、harden 和 workspace aggregate 连锁失败。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：当前本地成熟度控制面存在“检查覆盖、诊断输出、
  运行环境语义和成熟度声明不能由同一组可重放证据闭环”的系统性漂移。
- 触发证据：
  - `rtk bash scripts/check-all.sh --full`：52/58，6 failures。
  - 根 `tests/test_*.sh` 逐项执行：13/15。
  - `test_architecture_reports.sh` 正 fixture：`reports=0`，缺 product maturity
    audit、scorecard、report registry。
  - `rtk bash scripts/devkit.sh doctor --summary-json`：宿主 Python/依赖不支持。
  - `software-m5.sh status`：M5-ready，但 8 个 certification blockers。

## 目标
- 闭环根测试、门禁诊断、Python 入口与成熟度状态语义
- 提供统一根测试聚合入口，并由 full gate 强制执行。
- 失败检查输出有界、可定位、可机器读取，不再要求人工逐项复跑才能看根因。
- 明确 ADK Python 解释器选择、unsupported 环境行为和受支持验证入口。
- scorecard 显式区分 implementation level、evidence level 和 effective level。
- 对 dirty 参考仓与 strict ADK 做真实性分流，恢复当前工作区治理一致性。
- 对本地可落地范围完成定向、full、双 Python、source-to-live 决策和复审。

## 非目标
- 不伪造 Claude 凭证、第二位 operator、独立真实仓、30 天试点、远程 CI、
  attestation、push、tag、publish 或 final `3.1.0`。
- 不回退、删除或覆盖既有用户 dirty 变更。
- 不通过延长过期 baseline、弱化 strict policy 或修改 blocker 状态制造通过。
- 不修改 `~/codex` 与 `~/.codex`；若 mapped ADK 资产变化，仅形成明确的
  source-to-live 决策与待授权动作。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（dirty 所有权、共享 manifest、门禁递归、兼容）
- [x] 已明确验证命令与通过标准
- [x] 外部现场条件保持 blocked，不纳入本地完成声明

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：测试聚合、诊断、解释器入口和成熟度声明均属于平台中立
  控制面；不新增 runtime adapter 或场景插件。

## 变更重复性检查
- 已检索 `docs/changes/`、根 reports、现有 `check-all.sh` 和 ADK local-CI
  change；不存在相同 change-id。
- 历史 terminal hardening 已闭环 RC3/RC5 本地候选，本次差异是修复当前
  RC5 之后暴露的根测试覆盖、fixture 漂移、诊断和声明语义问题。

## Breaking Change 检查
- [x] 否：不删除既有命令；新增聚合与严格语义字段保持向后兼容
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：本 proposal 与 2026-07-23 成熟度审计证据。
- design 决策：`design.md` 的测试聚合、诊断、Python 与 scorecard 合同。
- tasks 追溯关系：`tasks.md` T1-T7，每项含 verify 和停止条件。

## 安装范围与依赖边界
- 安装范围：root/ADK project-bound；不自动进入 live target。
- 依赖边界：Bash、Python 标准库、既有 pinned Python 3.11/3.12 Docker
  工具镜像；不新增网络依赖。

## Prompt 回归证据计划
- 本变更不修改运行 prompt；Skill 只涉及既有 field evidence 内容。
- 失败样例保留在 `negative-results.md` 与对应 shell fixture。

## 收敛模式与退出条件
- 当前模式：execution。
- 退出条件：本地 blocker/major=0；外部 M5 blockers 仍被准确报告；两仓
  定向/full/双 Python 与 final-ready 有可重放证据。

## 备选方案与取舍
- 方案 A：继续依赖人工逐项运行根测试与失败检查。拒绝，覆盖不可证明。
- 方案 B：新增统一 root test runner、改进 full 诊断、补环境和成熟度机器
  合同，并保持外部 blocker。采用，变更可测试且不弱化门禁。

## 风险与回退
- 风险：聚合器改动可能改变 exit code；通过正/负 fixture 和 full 复验。
- 风险：scorecard 新语义与旧 consumer 不一致；只增加字段并保持既有字段，
  再用 current-status 与 product maturity tests 锁定。
- 风险：参考仓 baseline 误吸收用户变化；必须先读取 diff/hash/分类，不做
  自动清理。
- 回退：按文件恢复本 change 的最小 diff；不触碰用户原有 dirty 内容。
