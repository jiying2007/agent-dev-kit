# 设计说明：20261118-owned-build-session

## 架构影响
- Coordinator设计，独立实现者只写既有tests/test_skill_command_examples.py及验收测试，reviewer不写实现。没有产品公共API变化。
- Popen已有start_new_session=True，SID是本次拥有边界。快照按SID收集限定pid/ppid/pgid/sid/starttime/comm/state/cpu/wchan字段；维持原50ms/256entries/16records上限，缺失/有界观测显式降级。

## 身份与清理
- 保留leader身份锚；信号发送前复核PID/starttime/SID。Linux优先os.pidfd_open与signal.pidfd_send_signal并在打开后再核身份，避免PID复用窗口；不向未验证的其他PGID泛发信号。
- 原1秒cleanup总截止内处理已确认session成员。完成核对/终止成员前不主动wait/reap leader；保留原自有外组有界fallback。结束前检查存活成员、排空双流、回收leader。
- complete要求完整可用观测、无存活成员、双流排空与leader已回收。权限/身份异常、截断、缺失、不支持procfs/pidfd均保持保守状态，不把EOF当整个session退出证明。
- 原timeout仍抛AssertionError且保留两路输出和实际时间；诊断异常只降观测结论。

## 兼容性与迁移方案
- 原正常路径、15秒预算、ADC/CMake与CI全部不变。既有unavailable却assert complete的测试改为保守状态，是纠正错误断言，不削弱ADC性能验收。
- 不增加框架或依赖。兼容patch版本按既有规则同步；回退锚15fa31d1，正常受保护后继变更。

## 验证策略
- 真实Ninja sleep规则和无关独立session构成RED→GREEN；不mock真实反例。fake procfs/pidfd只用于难以安全制造的身份变化、权限/缺测分支。
- 定向CommandExampleRunnerTests、skill content后冻结候选，运行full/strict/format/release check/export并独立Spec/Quality。
- 原44116100760不再重跑。新修复是独立行为修复，不关闭历史超时；新候选若再超时保留SID现场，按新事实调查，不自动重试。专用诊断分支暂缓，避免无必要执行。
