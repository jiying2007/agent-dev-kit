# Prompt / Policy Before-After：intent-boundary-governance-v2

## Before

- Skill 只有 triggers/non_triggers 与 target 私有 metadata，缺少平台中立 invocation SSOT。
- task package 只声明 goal/action/verification，research、prototype 和 implementation 依赖自然语言区分。
- “检查架构”未给范围时可能扩展为全仓扫描。
- 原型保留依赖临时 branch/path 决定，缺统一 hash、expiry 和 cleanup owner。

## After

- `skill_invocation.default_mode + overrides` 是唯一调用模式事实；adapter 只做显式映射。
- task package v2 通过 kind、permission、exit gate 和 handoff 阻止探索直接进入实现。
- architecture 默认从用户范围、diff、近期热点和一阶依赖收敛；广域扫描必须记录理由。
- prototype 通过结构化 provenance 和 retention 合同保存，branch/worktree 仅为受治理例外。

## 正例

- “把四个独立研究问题并行取证，不改代码” → research + forbidden + evidence-reviewed。
- “根据已批准 spec 实现 T3” → implementation + approved + implementation-verified。
- “检查这次 diff 的架构风险” → broad_scan=false，范围为 diff + 一阶依赖。
- “显式调用只读设置向导” → explicit-only metadata；仍不自动获得写权限。

## 负例

- research + implementation_permission=approved → fail。
- prototype 缺 artifact hash/expiry/cleanup owner → fail。
- task package 声明 v1 或依赖默认补字段 → fail。
- Codex `openai.yaml` 顶层 `display_name` 或显式 implicit=true → fail。
- OpenCode/Hermes 收到未验证的 explicit-only mapping → fail closed。
- “架构优化”无用户范围却直接扫描全仓 → needs-fix，必须给 expansion reason。
