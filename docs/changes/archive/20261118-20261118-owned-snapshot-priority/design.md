# 设计说明：20261118-owned-snapshot-priority

## 架构影响
- 只修改既有tests/test_skill_command_examples.py的有限测试helper及验收。Coordinator设计/版本/证据，独立实现者写helper，reviewer只读实现。
- 原全局os.scandir(proc_root)没有自有优先保证；前256条目可以全部无关。先从SID leader出发，读各task/*/children，逐个读stat、筛SID和去重；剩余预算保留全局扫描以发现已经重挂父进程的同SID成员。
- 各线程children纳入有界发现；仅主线程不足以覆盖线程创建后代。任意PID列表不构成发信号授权。
- Linux官方procfs文档§3.7明确children只列一级，而且并发退出可能漏报其他子进程。因此children只提供优先发现线索，不能认证会话完整；剩余全局补扫与保守状态不可省。来源：https://www.kernel.org/doc/html/latest/filesystems/proc.html#proc-pid-task-tid-children-information-about-task-children 。

## 有界性与身份
- 2026-11-17T16:55:32Z的真实能力探针证实本地四个自有bash/Ninja/sh/leaf均有stat/task，但children文件ENOENT；首版fake-proc通过而真实前缀仍失败。设计据该新事实修订，不删除/skip真实验收，不假设hosted环境同样缺失。
- 既有cleanup已在同一1秒截止内重复调用snapshot；新增仅本次run使用的global迭代续扫context，防止每批从头和empty/bounded过早退出。每批仍50ms/256 entries，整个清理仍1秒。持有iterator必须在正常/异常/预算退出时关闭，不扩展为持久状态或新框架。
- 首批可用children优先提示；后续续扫已打开的global iterator，避免重复消耗相同无关前缀。不缓存无关PID，跨批实际owned记录至多16；诊断明确批次/有界原因，保留真实观测，不把后见结果伪写为首批。
- bounded/empty且仍可继续时继续下一批；全局穷尽或总截止才结束相应发现。前批partial/bounded保持保守资格；已核成员仍可终止，最终不把扫描完成冒充完整进程隔离。
- 枚举cursor穷尽不代表发信号后成员退出。若本轮pass发现live并发送信号，必须在原截止内以fresh pass/新鲜身份状态确认退出，不能复用耗尽iterator的空集。历史累积诊断不能用于新信号授权或伪装同时采样；没有进展或记录cap阻断时停止有界续行并降级，避免忙循环。
- 独立边界反例确认：global entry已advance后不能因额外计数丢弃numeric PID。一个global目录项及其stat使用同一已预留discovery单元，tree候选分别计数；若不能在该单元处理，必须有界保留续处理而不能静默丢失。第256个numeric位置与fresh pass构成固定回归，不增加256上限。
- 独立OSP-2确认最终资格还必须纳入累计report的保守状态。即使各批均observed，累计records或batch_results截断/非observed也不得complete；这不阻止对当前fresh合法记录安全清理。诊断累计状态与cleanup资格保持一致，不能仅看最后一批。
- 每批50ms、256 discovery entries、跨批16records与cleanup总截止不增加；候选PID、task/children边与全局条目共享单批计数/时间预算，队列有界；children以明确MAX+1读取识别截断，尾部半个PID不能当完整身份。
- 进程去重；自有树节点在遍历中消失/不可读不能证明无后代，应保守partial。全局未穷尽或其他观测缺口不能以定向树完结推断整个SID完结。
- 已发现合法成员必须保留并传给cleanup，即使global bounded也清理已核实成员；状态保持unverified/incomplete。
- pidfd及打开后PID/SID/starttime复核、leader未回收锚、外组fallback、双流和原timeout保持。可增加无敏感值的bounded原因，不能补写旧日志原因。

## 兼容性与回退
- 无产品公共接口/依赖变化，按现有patch规则同步11.4.2元数据。11.4.1尚无发行资格，不改写已合并历史。
- 已检索全部helper调用点，仅当前测试模块和归档原patch；没有动态公共调用面。回退走受保护后继变更，追溯锚main021d81aa。

## 验证策略
- 新验收在固定无关前缀下先RED再同文本GREEN。fake procfs/受控目录顺序只模拟顺序、截断、线程和缺测，不替代真实Ninja/信号验证。补不重开cursor、空有界批次续扫、总截止和迭代器关闭控制。
- 原真实Ninja测试文本及预算保持；实际进程、无关会话控制；单文件Ruff和完整示例模块后冻结clean candidate，既有八阶段/full102组，独立证伪与Spec/Quality。
- 原run44116100760重试额度耗尽，run44128721869不自动复跑。新源码另走required checks/main/Release；失败保留原件，不增加预算或自动重试。
