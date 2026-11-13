---
name: adk-verification-before-completion
description: "用于完成前核对测试、审查和真实证据；不用于把自述、静态检查或过期收据当作完成证明。"
version: 1.8.2
last_updated: 2026-11-14
triggers:
  - "准备完成"
  - "准备提交"
  - "完成前检查"
non_triggers:
  - 仅做方案讨论且尚未产生实现改动
  - 纯背景知识问答
inputs:
  - 改动清单、测试结果、评审结论、风险与回退信息
outputs:
  - 完成声明核对、Codify Decision、完成前核对清单、门禁结论、未闭环项与处理建议
constraints:
  - 没有验证证据不得给出完成或通过结论
  - 评审 blocker 未关闭时不得给通过结论
  - breaking change 必须显式声明与迁移/回退方案
  - 交付后沉淀决策必须记录 reusable_pattern、promotion_candidate、next_task_friction_reduced、reduced_by、reduction_evidence、do_not_promote_reason、owner_review、rollback_path、verification_evidence
---

# adk-verification-before-completion

## Goal
对明确的交付声明做独立、同快照、可追溯的完成验证。阶段里程碑和完整 Goal 终态分开，必要风险门禁不得因省 Token 或缩短报告而降低。

## Modes / Applicability
- **checkpoint（阶段验收）**：仅核冻结子项、受影响接口和真实 lint/test/build/smoke、Review、阻塞及后续依赖；不重复全 Goal final 或无关验证。只能声明阶段结果，不能关闭父 Goal。
- **goal-final（整个目标完成）**：核原始验收分母、全部交付和依赖、最终快照、独立验证、open items 与必要回归，符合所有适用门禁才声明 pass。
- **风险与阶段正交**：low 用最小充分证据；medium/high 即使是 checkpoint，也必须按实际风险完成权限、生命周期、模型/工具、UI、数据/发布等专项门禁。未知风险不能降级为 low。

## Workflow
1. **冻结来源与声明**：记录 scope/mode/risk、HEAD/source snapshot、原验收 IDs、claimant、verifier、变更与非目标。实现者自述、旧 CI 绿灯及源码推断不是独立结果。
2. **最短证据链**：核命令、exit code、环境、时间、raw pointer、适用 lint/test/build/smoke 与 Review blocker/major。失败/缺失/过期标 `needs-fix`，不得把未执行写成 pass。
3. **按风险启用专项门禁**：
   - 状态/共享资源/异步 → owner/state/event/resource/termination/invariant，取消/超时/恢复/晚到、generation 与 whole-lifecycle review。
   - 运行资产/配置/runner → 声明配置 vs `runtime_config_diff`、source-to-live、Runner Smoke Contract、真实加载/健康证据。
   - UI/主观 → Subjective Feature Proof + independent_verifier、Appshots / UI Evidence Boundary；源码检查不替代运行态结果。
   - prompt/policy/skill routing/model/context → Trace Eval Regression Evidence 或真实 `not_applicable_reason`；MCP/hook/permission/approval/sandbox → Runtime Control Plane Audit，核 allow/deny、loaded_tools、rollback_path。
   - 中高风险、协议/数据/安全/发布 → Replayable Evidence Bundle、Tool / Skill Evidence Plan、Completion Guard Payload、迁移/回滚和适用的运行环境证据。
4. **审查收敛**：验证需求/契约基线、Review Convergence Evidence、design-change/replan、skipped skills 与 fallback evidence。高风险关键范围 `uninspected` 时不得凭局部复核宣称整体通过。
5. **结论/沉淀**：检查 required artifacts、open items、证据新鲜度与权限。checkpoint 只报告已完成子项与剩余验收分母；goal-final 按适用性处理 Codify Decision，不满足复用价值/owner 审核写 `do_not_promote_reason`，不能声称 `promotion_candidate: true`。结果 `pass | needs-fix`，附风险与下一步。

完整 Applicability Matrix、25-step 解释、证据字段及高风险模板按需见 `references/verification-governance-details.md`；高风险、完成争议或证据缺失必须回读相关规范和原文。

## Evidence Template（最小入口）
```md
- Scope / Mode / Risk: checkpoint | goal-final / low | medium | high
- Claimant / Verifier / Snapshot / Original Acceptance IDs:
- Applicable Checks: command / exit_code / verified_at / raw_evidence
- Review Status (B/M/m) / Open Items / Missing Evidence:
- Applied / Skipped With Reason / Unchecked Scope:
- Subjective Feature Proof: independent_verifier / expected / observed / verdict | not-applicable
- Appshots / UI Evidence Boundary: runtime_evidence | not-applicable
- Runner Smoke Contract: identity / execution / failure_cancel_path | not-applicable
- Runtime Control Plane Audit: loaded_tools / approval_boundary / deny_path_test / runtime_config_diff / rollback_path | not-applicable
- Trace Eval Regression Evidence: source_trace_id / grader / not_applicable_reason
- Replayable Evidence Bundle: source_snapshot / tool_transcript / artifact_hashes | not-applicable
- Tool / Skill Evidence Plan: primary / supporting / skipped skills / fallback_evidence | not-applicable
- Lifecycle Operation Evidence: contract / owner / termination / runtime_evidence | not-applicable
- Review Convergence Evidence: review_round / finding_classes / reviewer_independence / replan | not-applicable
- Completion Guard Payload: required_checks / passed_checks / skipped_with_reason / stale_checks / verifier
- Codify Decision: reusable_pattern / promotion_candidate: true | false / do_not_promote_reason / owner_review / rollback_path / verification_evidence | checkpoint-deferred
- Final Gate Result: pass | needs-fix / qualification_boundary / next_action
```

## Failure Handling / Quality Gate
- 任一适用必需项失败、无有效理由跳过、证据过期、Review blocker/major 未闭环或独立 verifier 缺失 → `needs-fix`；不得填空表掩盖缺口。
- 运行态配置、Runner、权限、MCP、UI、发布或真实设备门禁需要现场/宿主证据时，缺失只能写未验证；`completion_coverage` 的静态 pass 不等于运行认证。
- 生命周期缺 owner/终止/真实边界、设计变更未 replan、重大 Review 未独立闭环不得通过；breaking change 必须有迁移与回退。
- `Codify Decision:` 仅在适用的最终交付/复用晋级时记录 reusable_pattern、promotion_candidate、next_task_friction_reduced、reduced_by、reduction_evidence、do_not_promote_reason、owner_review、rollback_path、verification_evidence；没有真实效果/owner review 不晋升。
- 预算检查、组件发布和产品/现场资格是独立状态；阶段通过不赋予 commit/merge/release 权限。输出实际命令、证据、剩余风险和结论，禁止“应该通过”。
