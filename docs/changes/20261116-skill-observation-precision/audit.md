# 其他 Skill 的分组复查与采用决定

基线：ADK 11.3.11，commit `fad9d4d170a97c5dbb2c5261432fa2120bfcc3c9`。本轮不重复修改上一轮五个 Skill。

本轮三个分组共复查 23 个其他 Skill：2 个 ENHANCE、20 个 KEEP、1 个 OBSERVE。KEEP 表示本轮在已列范围内未建立新缺口，不表示对所有运行环境作出认证。完整阅读范围、命令、源码 hash、原始探针和来源在 `evidence/audit-bundle.json`，逐文件以 gzip+base64 无损保留；解码后按 bytes/sha256 检查。

| 分组 | 本轮结论 | 依据与边界 |
| --- | --- | --- |
| 嵌入式实现：driver-implementation、driver-bringup-checklist、interrupt-dma-patterns、protocol-stack-integration、register-map-design、rtos-task-design | 6 KEEP | 已覆盖部分初始化与迟到完成、主动探测副作用、DMA所有权/一致性、流式边界、resetMask已定义位、RTOS量化/绝对周期；8项定向回归通过。未执行硬件测试。 |
| 诊断与验证：systematic-debugging、hardware-debugging、embedded-remote-debug-log-triage、offline-core-dump-triage、performance-profiling-embedded、fault-injection-recovery、integration-hil-sil、unit-test-embedded、embedded-diagnostic-harness | 1 ENHANCE、7 KEEP、1 OBSERVE | 采用 fault-injection-recovery 的实际命中方法；harness 未定位真实响应消费器，保留观察；其余未建立新的可复现缺口。 |
| 任务与取数：data-fetch、email-imap-fetch、fetch-url-content、requirements-triage、structured-requirements-questioning、lightweight-planning、task-breakdown、goal-authoring | 1 ENHANCE、7 KEEP | 采用 email-imap-fetch 的精确时间方法；其余已覆盖本轮检查的预算/partial、重定向、输入就绪、计划及任务边界。 |

表中名称省略统一的 `adk-` 前缀；email-imap-fetch/fetch-url-content 的实际路径在 optional-skills/adk-data-fetch 下，父 Skill 不自动安装子 Skill。

## 采用的受控观察

故障注入 host C 探针使用 GNU ld malloc/free 包装，正常、配置但未命中、实际命中、错误清理变体的进程均退出 0。配置第3次分配失败但实际只分配2次时，命中计数为0；错误清理变体即使后续输出42仍残留1个 allocation。方法因此需要把配置、实际命中、检测与恢复分开，并在解除故障后检查功能、数据和资源。这不是 ADK 自带运行态判定器的漏洞复现。

IMAP 探针使用 CPython 3.12.14 的 imaplib.IMAP4_stream 与本地 stdio 夹具。精确 UTC 日窗口下，受控 ±02 时区输入使单纯日级搜索产生时间误取和漏取；Date 与 INTERNALDATE 的对照表明两者不能互换。缺失 INTERNALDATE 样本保留已成功项与未判定 UID。完整地址筛选也有独立研究观察，但不纳入本轮实现；新回归必须隔离时间条件。已知夹具的日期扩展不构成任意时区范围的通用算法。

原始探针没有覆盖命中证据缺失、非法时间、未知时区和预算实际耗尽；这些是设计要求的新回归，不把既有探针说成已完成验证。普通日级兼容也须由实际日级路径验证。

## 采用边界

仅修改两个现有入口和对应测试、现有版本派生元数据。故障注入入口总字节不超过基线3559；不提高任何 Profile 限额。保留授权/隔离/独立操作者、资源预算、停止/回滚、回执、SLA和邮箱只读/UID/预算要求。无设备写入、真实邮箱连接、新运行时依赖或付费模型任务。单次方法消费观察不用于宣称 native/HIL、服务器一致性或成本/Token收益。
