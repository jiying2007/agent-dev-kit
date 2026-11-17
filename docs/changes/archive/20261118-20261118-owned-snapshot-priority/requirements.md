# 需求：20261118-owned-snapshot-priority

修复有界全局 procfs 扫描可能在读取本次自有后代前耗尽条目预算的问题。前次 main021d81aa 的真实 Ninja 回归失败原件保留；其 bounded 具体触发原因未记录，不能当成已证实宿主进程数或时间原因。

- ACC-001：至少256个无关目录条目排在自有进程前时，在原清理总截止内续扫并发现同SID后代，包括Ninja新PGID；可用的各线程children仅作优先线索，缺接口不能从头反复扫描或跳过真实验收。去重并拒绝其他SID，不读取argv、环境或内存。
- ACC-002：保持work=15s、cleanup总截止=1s、每批快照50ms/256 discovery entries/16records；定向和全局共享单批预算，cleanup仅在原总截止内继续下一批。children读取有字节上限；跨批合并实际观测最多16records，不积累无关PID；iterator在结束/异常关闭。截断、缺测、身份变化及不完整观测不得报告complete。
- ACC-003：原真实Ninja验收逐字不弱化；返回后已发现自有后代无live进程，无关会话存活。发现不构成信号授权，既有pidfd打开后PID/SID/starttime复核保持。
- ACC-004：正常退出、双流、原timeout、外组fallback、缺能力拒绝不回归；旧失败与实际RED/GREEN保留，定向、精确候选full和独立Spec/Quality有实际证据。

非目标：不改变ADC/CMake、测试顺序、CI、门禁、时间/数量上限、模型或设备资格；不保证主动另建SID的进程隔离；不称旧ADC15秒等待根因修复。发行与Root仅使用新候选自己的真实通过证据。
