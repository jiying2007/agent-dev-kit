# 设计与边界

atomic_io管理共享strict object JSON编码与安全text publication；installation_contract保留私有wrappers及既有schema/预算/事务。campaign复用两者并使用regular_only reader；source archive与runtime bundle两条release checksum通过同一writer显式0644，旧隐藏fixedtmp不读取/清理，output leaf链接拒绝。archive与checksum不是一个原子事务，checksum失败可留候选archive，但不会返回成功或覆盖外部链接目标。lock acquire元数据用同一private writer，已有owner目录/newlock失败清理及expected lock_id机制保留。

锁超时只接受有限非bool数值0..300，先type/range再isfinite避免巨整数overflow。锁文档严格decoder、regular descriptor、typed非空strings/positive integerPID/aware timestamp；未知/溢出pid failclosed。EPERM代表进程存在且不可据此clear；ESRCH才表示不存在，其他OS错误不伪造dead。本机unknown probe无论age均拒clear；真正remote stale加expectedID机制保留。stale阈值非bool非负integer。

调用方控制parent和writer；不是防同权限任意并发/parent rename或整事务断电日志。默认0600已在8.0.1安装文档采用，本包扩展campaign/lock；public checksum0644。正常API/schema不迁移，非法输入变为ManifestError；patch source8.0.2同步七projection。

官方参考：[Python tempfile](https://docs.python.org/3/library/tempfile.html)、[math.isfinite](https://docs.python.org/3/library/math.html#math.isfinite)。验证调度成本另项评估，不以未实测线程池宣称速度收益。回滚基线46c35605/8.0.1，回退会恢复已实证的固定临时路径风险。
