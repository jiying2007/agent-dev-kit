# Embedded Remote ADB/HIL Hardening Tasks

- [x] T1 更新 `adk-embedded-remote-debug-log-triage` 的健康分层、失联熔断、身份和 HIL 契约。
  - Verify: `rtk rg -n "READONLY_PREFLIGHT|adb devices -l|circuit breaker|ARTIFACT_GATE|SHORT_CYCLE|RESTORE_HEALTHY_STATE" skills/adk-embedded-remote-debug-log-triage/SKILL.md`
- [x] T2 修正 `adk-runtime-router` 下游命令，删除不存在入口。
  - Verify: `rtk rg -n "skill-search.sh|test_agent_routing_eval" skills/adk-runtime-router/SKILL.md`
  - Negative verify: `rtk rg -n "scripts/devkit.sh match|check-runtime-routing" skills/adk-runtime-router/SKILL.md` 预期无匹配。
- [x] T3 更新 skill README 与变更证据。
  - Verify: `rtk bash scripts/devkit.sh validate --strict`
- [x] T4 导入 `~/codex` 新版本并运行 source-to-live。
  - Verify: 由下游 `~/codex` 完整 build/doctor/plan/apply/check 提供。
