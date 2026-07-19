---
name: external-practice-absorption
description: 多来源外部实践从 report-only candidate 到独立决策、ADK change、验证、pilot、发布复审和退役的治理工作流
version: 1.0.0
last_updated: 2026-07-19
primary_agent: external-practice-curator
primary_skill: adk-external-practice-absorption
triggers:
  - "吸收外部实践"
  - "Gitee GitHub GitLab 实践评估"
  - "Codex Claude 官方实践吸收"
  - "从参考实现生成 Agent Skill Workflow"
profiles:
  - research-intake
command_risk: low
stages:
  - discover
  - normalize
  - triage
  - decide
  - propose
  - implement
  - verify
  - pilot
  - publish
  - review-retire
artifacts:
  - external-practice-candidates.jsonl
  - cycle-evidence.json
  - curator-review.md
  - owner-decisions.jsonl
  - proposal.md
  - verify-report.md
  - pilot-report.md
  - retirement-review.md
verification:
  - "rtk bash scripts/devkit.sh validate --strict"
  - "rtk bash scripts/check-workflow-closure.sh --profile research-intake --with-optional-skill adk-external-practice-absorption"
failure_handling:
  - "来源、license、版权或 provider 状态不完整时停在 triage"
  - "没有独立 owner decision 时不得 propose"
  - "没有验证和 pilot 时不得 publish"
---

# external-practice-absorption

## Goal

- 统一 GitHub、GitLab、Gitee、官方文档、微信公众号和人工证据的吸收闭环。
- 保持 provider 只负责 metadata adapter；所有来源共享 candidate、decision、安全、验证和退役合同。
- 通过明确人工 gate 防止“采集即吸收”“官方即自动采纳”和自评自批。

## Scope

- 适用于公开 forge metadata、官方文档 manifest、微信 metadata catalog 和 allowlisted 人工 URL。
- 自动阶段只到 candidate/queue/evidence；不包括第三方代码执行、自动 owner decision、安装、commit、push、publish 或 live apply。

## Ownership

- Primary agent：`external-practice-curator`，只读整理与建议。
- Primary skill：显式安装的 optional `adk-external-practice-absorption`。
- Decision owner：独立人类/治理 owner；不得是 curator 或 collector。
- Implementer / verifier / publisher：按 change 交给既有 ADK delivery 角色，权限不由本 Workflow 扩张。

## Stage Contract

1. `discover`：显式 source plan；网络必须单独授权，只读 metadata，生成 transport evidence。
2. `normalize`：只接受 `external-practice-candidate/v1`；固定 `review-required`、`body_persisted=false`、`auto_actions=[]`。
3. `triage`：核验 source、freshness、duplicate、license/copyright、security、architecture、维护成本和不可迁移缺点。
4. `decide`：独立 owner 写 `ADOPT|MERGE|ENHANCE|OBSERVE|REJECT`；这是人工 gate。
5. `propose`：只有前三类批准决策可创建 ADK change，并写 breaking/installation/dependency/test/pilot/retire 合同。
6. `implement`：由正常实现角色执行；curator 不写实现，不从第三方 silent copy。
7. `verify`：运行定向、strict/full、安全、性能和负例；fixture 不得冒充 live/pilot。
8. `pilot`：在受控范围验证真实增益、成本和回退；无授权时保持 `not-run`。
9. `publish`：独立 review 通过且用户显式授权后，才走 version/source-to-live/commit/publish；这是人工 gate。
10. `review-retire`：按 expires/review_after/usage/eval 复审；失效或重复资产明确退役并清残留。

## Gate Matrix

| Gate | 必须证据 | 未满足动作 |
|---|---|---|
| Source | URL、revision/hash、retrieved/expiry、authority、transport | 停在 discover/normalize |
| Legal/Security | license/版权、供应链、prompt injection、token/正文边界 | `OBSERVE|REJECT` |
| Architecture | 现有资产重复检查、平台边界、MERGE/ENHANCE 理由 | 返回 triage |
| Decision | 独立 owner、日期、理由、目标、evidence refs | 禁止 propose |
| Verification | tests、negative results、Prompt before/after、review | 禁止 pilot/publish |
| Pilot | 真实或明确 not-run 的效果、成本、回退 | 禁止 publish |
| Retirement | owner、review date、expiry、rollback/removal gate | 禁止长期 active |

## Artifact Contract

- `external-practice-candidates.jsonl`：统一 v1 candidate；不得含正文、token、auto action 或批准状态。
- `cycle-evidence.json`：每个 job 的 fixture/live/local、host/path、状态、候选数、hash、degraded/error 和边界。
- `curator-review.md`：优点、不可迁移缺点、重复、安全、架构、成本和负结果。
- `owner-decisions.jsonl`：与 candidate 分离的独立 owner decision。
- `proposal/verify/pilot/retirement`：只在对应阶段有真实证据时创建，不用空文件冒充完成。

## Commands

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash scripts/check-workflow-closure.sh --profile research-intake --with-optional-skill adk-external-practice-absorption
rtk bash tests/test_optional_skills.sh
rtk bash tests/test_workflow_closure.sh
```

## Failure Handling

- Gitee 空结果保留 `degraded-empty`；不把候选数 0 当作来源健康。
- 任一 provider transport error 只影响该 job，但 cycle 必须显式 degraded/failed，不能静默跳过。
- owner 与 curator 不独立、decision 缺字段或目标不清时，固定 `needs-fix`。
- 与现有资产重叠而无净增益时，选择 `MERGE|ENHANCE|OBSERVE|REJECT`，不新增平行资产。
- 发布权限缺失时停在 verified/pilot-ready；不自动 commit、push、apply 或 publish。

## Exit Evidence

- candidate/decision/change ID 可双向追溯。
- 明确吸收优点、拒绝缺点、目标资产形态、安装范围和依赖。
- blocker=0、major=0，定向与全量验证有命令级 Evidence Index。
- pilot、发布或 source-to-live 未执行时明确 `not-run` 及影响。
- review/retire owner 和日期已记录，无旧入口、兼容层或孤儿资产残留。

## Quality Gate

- Candidate 与 decision 分离，curator、owner、implementer、verifier/publisher 权限不自循环。
- 所有来源共享同一 gate；Gitee `degraded-empty`、官方平台边界和微信正文边界均有负例。
- optional Skill 必须显式选择，`research-intake` Workflow 在缺少该 Skill 时 fail closed。
- blocker=0、major=0 且 completion evidence 与声明一致后，才允许结束 Workflow。
