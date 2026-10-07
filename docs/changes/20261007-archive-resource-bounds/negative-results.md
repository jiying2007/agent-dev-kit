# 负结果与边界

- 8.0.3校验器在74,507字节/零载荷归档上缓存12,000个成员后才因missing critical拒绝，JSON8MiB约束不覆盖metadata；以原源码实际复现，不将其冒称完整有效制品PASS。
- 新增12项确定性entrypoint tests通过；覆盖预算、隐藏PAX、CRC/截断、concat解压、critical成员、实际提取前无mutation、same snapshot/path replacement及叶节点特殊类型。原14严格JSON通过；正式8.0.3实际archive兼容且SHA86f1f591d9c8f528d2586cd47417edcfb2aa3ffb118e51893c3d53588d1e1ede不变。
- 尚未完整回归/密码学发行或声明Root消费；完整验证按freeze source/index实际终态判定，旧结果不能替代。
- 字节/record预算不证明墙钟时间或精确RSS上限；OS级限制和caller对parent/writer控制仍必要。
- quick预检首先在SIM117 nested with处失败，修复后重跑；初版a187a37...source/index旧receipt不可计最终通过。
- 首次readonly review：Major真实rehearsal仍无界hash/resolve/double-read，Minor1200隐藏PAX header递归异常（2764压缩bytes）；已加入真实入口snapshot/checksum/上传同bytes以及header链预算、异常归一测试。
- 自检global PAX映射的逐TarInfo缓存放大，新增缓存<=1测试、metadata请求/累计/键上限；现在19定向全部通过。不得复用旧12测试freeze或提前声明full通过。
- CLI最终caller仍resolve，补expanduser与真实coreCLI拒绝链接回归；现在20archive定向、14JSON通过。mypy修复为最小read Protocol及getattr/list guard的cache协议，不使用ignore或unsafe fallback。
- same-source quick两次56/56、strict/lint/types均通过但140952ms/143806ms超既有120000ms。串行对照正式8.0.3 exact3df、相同pinned3.11镜像、隔离只读worktree基线也56/56且139422ms超限；说明基线同样存在耗时超限，不能冒充quick全通过或仅归因新增解析。保留上限不改，full按独立1800s预算验证；墙钟优化独立待定位，不声明吞吐收益。
- baseline工作树.worktrees/adk-archive-perf-baseline-20261007 clean/detached、base3df，仅用于对照，本轮保留不删除；不改当前staged源码或用户dirty。
- 首次full于Python3.8 focused types失败：旧tarfile.open overload要求IO[bytes]而read-onlyRawIO不匹配；改为raw TarFile构造器明确文件对象protocol，metadata可选map保持guard。定向同pinned3.8 mypy五distribution模块PASS、20entrypoint testsPASS，不使用ignore。旧full源68e...作废，终止仅own runner1332553/容器088353f0a9a8，exit143；日志/tmp/adk-804-py38-type-negative-20261007.log保留，最终新freeze重跑。
