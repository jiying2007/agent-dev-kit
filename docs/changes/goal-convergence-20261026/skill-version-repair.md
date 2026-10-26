# 技能来源版本补齐

正式导入8.1.0时，Codex受管导入器拒绝8个内容已变化而版本未增长的技能。对比exact 8.0.2与8.1.0 Git tree，涉及既有路由描述、措辞和接口契约说明变更；这些内容不是本次8.1.0新增。本次只为各技能提升一个patch版本，产品版本提升8.1.1，保留导入器严格约束。

范围：adk-archive-governance 1.0.1、adk-commit-pr-quality-gate 1.1.1、adk-interface-contract-design 1.3.3、adk-knowledge-archive 1.0.1、adk-release-versioning 1.4.1、adk-requirements-triage 1.3.1、adk-task-breakdown 1.4.2、adk-unit-test-embedded 1.1.1。技能正文、执行引擎、权限、目标验收与运行时能力均不作行为变更。

验收：8个SKILL.md对8.1.0的差异仅version一行；strict、技能目录与版本一致性门禁通过；独立审查及Harness凭据绑定当前源码；protected CI全矩阵通过后生成签名凭据；Codex正式导入器重新执行dry-run并通过。若任何其他同版本变化被检出，保留失败并具体处理，不绕过或手改镜像。

回滚：保留先前发布和exact source commit；不得移动已有tag或将新内容标成历史版本。源码打包、Codex安装和GROS工程验收独立报告。
