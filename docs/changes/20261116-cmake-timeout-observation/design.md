# 设计

职责：parent冻结需求和设计；diagnose_adc实现；另一个只读Agent独立审查。

在现有CMake fixture中使用Bash内建EPOCHREALTIME作为PS4前缀并开启VERBOSE，保持从SKILL.md提取的代码不变。只在已发生TimeoutExpired后记录本次Popen会话/进程组的Linux procfs快照；字段仅PID、PGID、state、comm、CPU计数及wchan，禁止argv/environ。给快照明确的条数和短时间上限，与原1秒清理截止时间共用预算；读取失败降为诊断不可得，仍执行原kill/reap及抛错。不得诊断全机或为成功路径增加轮询。

回归使用真实独立进程组与可控sleep；同时建立不相关组和含敏感标记的参数/环境，确认快照不泄漏且清理不误杀。保持正常退出0/7控制和缺procfs、进程竞态的错误路径。

这只是观测增强，后续根因修复必须由新证据支持。回滚为撤销本change的fixture修改，旧失败及证据仍保留。仓库已授权source-only执行；~/codex不可用，宿主知识与执行策略门禁未运行，不作为通过。外部读写使用既有GitHub connector、限定jiying2007授权仓库/PR，拒绝密钥/运行态目录写入，失败退回本地保留成果，不伪造回执。
