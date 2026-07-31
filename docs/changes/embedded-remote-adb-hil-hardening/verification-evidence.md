# Embedded Remote ADB/HIL Hardening Verification Evidence

验证日期：2026-07-26

## Positive Path

- ADK：
  `rtk bash scripts/devkit.sh validate --strict`
  通过。宿主 Python 3.8.10 不在发布支持范围，因此此项仅作为开发门禁证据。
- PCR02 项目：
  `rtk python3 -m unittest discover -s codex_assets/tests -p 'test_*.py' -v`
  通过，7/7。
- Codex 路由：
  `rtk python3 -m unittest tests.test_agent_routing_eval -v`
  通过，3/3。
- Codex skill：
  `rtk bash scripts/check-skills.sh`
  通过，`skills=63 errors=0 warnings=0`。
- Codex source-to-live：
  build、doctor、plan、同计划 dry-run、apply、routing precedence 和全量
  `scripts/check.sh` 均通过；最终 `diff.sh` 为
  `same=440 diff=0 missing=0`，`drift.sh` 为
  `status=ok changed=0 stale=0 unmanaged=0`。
- Knowledge Hub：
  `knowledge-check.sh --dry-run --json --explain` 通过，
  `status=pass`、`errors=[]`、`warnings=[]`。

## Negative Path

- 无默认现场端点；没有用户或环境提供 endpoint 时拒绝执行远程连接。
- `adb connect` 不信任退出码，按输出语义和 `adb devices -l` 状态复核。
- 不可达 preflight 仍独立执行 network hint 与 ADB transport 探测，随后打开
  circuit breaker，禁止进入写操作。
- deploy 未显式确认时，在任何设备访问前拒绝。
- deploy dry-run 离线且不产生远程 mutation。
- 制品身份不一致时，artifact gate 阻止部署。
- 现场写操作只允许进入显式授权的 mutation stage；失联、core、fatal log、
  supervisor 重拉起或健康恢复失败均停止扩大 HIL。

## Evidence Boundary

- 本次未连接真实设备、未 push、未 kill/restart、未 remount、未部署、未回滚，
  也未执行真实单机/短循环/长压测。
- 因此只声明治理资产、工具离线测试、路由和 source-to-live 同步通过；不声明
  现场固件、设备恢复、真实性能或 HIL 验收通过。
- 真实板级闭环必须从 `READONLY_PREFLIGHT` 重新开始，并保留设备侧 evidence
  bundle、artifact identity、backup anchor、postcondition 与最终健康恢复证据。
