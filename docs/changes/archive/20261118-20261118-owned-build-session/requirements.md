# 需求：20261118-owned-build-session

修复既有构建示例 helper 的同 SID / 异 PGID 观测、清理及清理结果误报，保持原验收和资格门禁。

- ACC-001：真实 Ninja 新 PGID 后代被完整快照发现；只读限定状态字段，不读 argv/环境/内存；无关会话不采集。
- ACC-002：超时后自有会话存活后代退出，无关独立会话存活；信号依赖新鲜 PID/starttime/SID 身份核对，Linux 优先用标准库 pidfd 防重用窗口。身份漂移、缺权限、缺测/截断、未排空双流或未回收 leader 均不报 complete。
- ACC-003：正常退出码、stdout/stderr及原 timeout 失败保留；默认work=15s、cleanup总期限=1s、单次诊断50ms/256entries/16records上限不变。诊断错误不覆盖原timeout，不阻止原自有外组的有界fallback。
- ACC-004：固定真实反例基线RED→新GREEN，无关session负控制，身份/缺测确定性分支；共享helper full与独立审查有实际证据。

原hosted ADC/CMake超时原因仍UNKNOWN。主动脱离本次SID的守护化/恶意进程不在此有限helper保证内，不能把session清理称为任意进程树隔离。单次新head通过不证明历史超时原因解决或总体稳定性。
