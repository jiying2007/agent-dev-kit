# 评审报告：adk-terminal-contract-hardening

- 时间：2026-07-18T07:30:00Z
- 执行人：Codex（AI 第一轮复审）
- 结果：local-pass-external-blocked
- 分级统计：blocker=0 major=0 minor=0 question=0

## 必改项

- TC-001 至 TC-004 均已修复并有定向回归；无未闭环 blocker/major。

## 真实性裁决

- 根 full 红项保留：未提交 candidate、旧 release evidence digest 和 strict dirty 状态不得用本地 fixture 消除。
- 当前解释器/依赖不受支持：doctor 返回 fail 是真实边界。
- AI review 不替代 owner 对版本、发布、远程运行和业务语义的签收。

## Core/Optional 归属

- 归属：core control plane。
- 理由：manifest、installer、validation、performance 和 supported environment 影响所有 profile/target；未新增 Skill 或 live runtime 安装。

## 2026-07-18 CI waiver continuation review

- 结果：needs-fix。
- 分级统计：blocker=0 major=4 minor=0 question=0。
- 必改项：TC-005 至 TC-008，详见 `review-findings.md`。
- 真实性裁决：双版本 full matrix 的功能结果真实，但其首轮容器权限/网络/镜像身份边界不足，不能作为最终替代证据；修复后必须在新源码快照上重跑。

### 修复后复审

- 结果：local-pass-external-blocked。
- TC-005 至 TC-008 全部 fixed；复审后 blocker=0、major=0、minor=0、question=0。
- 最终替代证据使用 source snapshot `33ab17d4ef6b21e3bb7a7cce2a58bb04ae437a4789dba621bf3fd74970e1a2ac`，Python 3.11/3.12 各 54/54，两个独立 dependency audit 均通过。
- AI review 仍只作为第一轮风险扫描；owner 对 commit/version/发布与外部认证的签收未被替代。

## RC3 release closure review

- owner 已明确授权本地 commit/version/rehearsal；不包含 push、tag、publish 或 live apply。
- exact-commit 双构建、sidecar、rc.2 → rc.3 rehearsal 与 54/54 full 均通过；本地 release blocker=0、major=0。
- RC2 artifact 不能从其声明 commit 精确重建的问题已记录为历史 provenance 缺口；RC3 通过排除 `*.log` 与归档负例防止复发。
- 结论：`local-release-pass-external-blocked`。远端 CI/attestation、真实 runtime、独立操作者和 30 天 field evidence 仍阻断认证与 final 3.1.0。
