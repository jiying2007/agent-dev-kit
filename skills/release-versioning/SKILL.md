---
name: release-versioning
description: 版本策略、变更说明与发布基线
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 里程碑发布、量产切版前
  - 分阶段迁移切换前
non_triggers:
  - 开发中临时调试
inputs:
  - 版本号策略、发布目标
outputs:
  - 发布清单与版本说明模板
  - 阶段门禁决策（baseline-aligned/migrate-ready/cutover-ready）
constraints:
  - 必须记录可回滚版本
  - 阶段式迁移必须记录每阶段回退锚点
---

# release-versioning

## Goal
- 统一版本语义与发布清单，降低升级和回退风险。

## Prerequisites
- 确认版本策略（SemVer 或项目定制规则）。
- 收集本次发布范围、变更类型与受影响用户。

## Workflow
1. 版本决策：根据变更类型确定 major/minor/patch。
2. 变更归档：按 feat/fix/refactor/docs 分类生成 changelog。
3. 发布清单：制品、依赖、配置变更、迁移步骤。
4. 阶段矩阵：给出里程碑阶段、退出条件、验证证据与回退锚点。
5. 回退预案：可回滚版本、触发条件、验证命令。
6. 发布签署：输出 go/no-go 结论与残留风险。

## Commands
```bash
git tag --list | tail -n 20
<release-verify-cmd> --version <new_version>
```

## Evidence Template
```md
- Version Decision:
- Change Summary:
- Artifact List:
- Stage Gate Matrix:
- Migration/Rollback Plan:
- Release Gate Result:
```

## Failure Handling
- 版本号与变更类型不匹配时，停止切版并重审。
- 缺失回退路径时，结论必须为 `needs-fix`。

## Quality Gate
- 必须给出版本号决策依据。
- 阶段式迁移必须给出阶段结论与回退锚点。
- 必须附完整迁移与回退步骤。
- 必须明确发布门禁结论与签署条件。
