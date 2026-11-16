# 独立 Spec / Quality 审查

**结论：Spec PASS，Quality PASS；无未解决阻断或新增发现。** 本结论限定为冻结源码审查，不替代后续受保护 PR/main CI、发布与 Root source-only 接入。

- Reviewer：`ai/root/embedded_methods`，未参与实现；辅助机械检查者为 `ai/root/embedded_methods/evidence_binding_check`。
- Reviewed at：`2026-11-16T14:55:14.993112+00:00`。
- Evidence completed at：`2026-11-16T14:51:02.383334+00:00`（本次最后完成的实际执行为精确源码 full；之后仅做回执/摘要核验）。
- Base：`fad9d4d170a97c5dbb2c5261432fa2120bfcc3c9`。
- Reviewed commit：`384bdcdfac75881891bce795991b68fa46d9b9d6`；tree：`627aabff2317705de46b010126edf3b57a443d1f`；版本 `11.3.12`；45 个变更路径。
- Patch：451173 bytes，SHA256 `ae27a8e2e298f8f4e98290adba4f2e2d4609d5a3d29a1eea11edbac8172e4823`。
- 审查过程未写 repo/index/ref，最终仍 clean detached。

## 判定依据

F1 已区分配置、实际命中、检测与恢复。未命中与 `hits=None` 不会借错误返回或正常 follow-up 升级；命中后只进入检测和恢复检查，不返回整体 pass。没有时钟证据时保留 unknown，不填零时延或判 SLA 通过。目标身份、隔离授权、独立设备操作者、资源预算、恢复/回滚、停止条件、功能/数据/资源后置条件保持。文件为 **3558 bytes ≤ 3559 bytes**。

F2 仅增强精确时间请求。普通日级路径实际执行，时间基准、时区、区间与候选覆盖依据明确；INTERNALDATE 与 Date 不互换；缺失、非法、未知时区及数量/字节预算耗尽均保留成功项与未判定 UID，结果 partial。新回归所有 sender 相同，没有把旧探针的完整地址条件带入生产范围。

| 验证 | 实际证据与结果 |
|---|---|
| 独立精确源码重放 | 13 项测试 PASS，0 skips；保留完整 argv/stdout/stderr/exit/time。 |
| 坏变体拒绝 | 忽略命中证据、包含排他上界、使用 Date 替代所选字段、给未知时区补 UTC 四种 scratch 变体均由原行为断言拒绝；不是 import 或缺 marker 的假失败。 |
| 精确源码 full | 102/102 组 PASS，exit 0，未超时，379.451354s；前后 HEAD/tree/index/status 一致且 clean；日志 bytes/SHA256 与回执一致。13 项新测试在 full 的 stderr 中均为 ok。 |
| 冻结前定向与构建证据 | 14 项共同检查、strict、八个原 Profile ratchet、真实 Claude Code 导出均已有真实回执，并按逐文件摘要绑定当前源码；不追认其曾在最终 commit 上执行。 |
| 机械交叉检查 | Manifest 除版本外不变，原阈值逐字不变；40 项归档可独立解码并核 bytes/hash；99 个实际导出 payload 与 manifest 匹配；两份 Skill 导出正文等于当前源码。 |
| 单次消费者 | 原输入与结果已审：B 未命中，C 只支持有限 host 后置条件，D 资源恢复失败，时间/SLA 未知。邮件返回101/102/104/106/107/108/201、排除103/105、202未判定，partial；未偷换 Date 或增加 sender 条件。 |

## 证据与实际阅读范围

完整机器报告：`/workspace/scratch/2d4d08f07657/other-skills-independent-review.json`。

原始独立重放与坏变体证据位于 `/workspace/scratch/2d4d08f07657/other-skills-independent-probes`：

- `review-probes.py`：实际重放、四种受控替换及完整记录逻辑。
- `receipt.json`：所有命令原始输出/退出码/时间、45 路径源码摘要、正常与预期拒绝结果。
- `source.patch`：上述 base→reviewed commit 的完整 binary/full-index diff。
- `ignore-activation-evidence.md`、`include-end-boundary.py`、`use-date-instead-of-selected-field.py`、`invent-timezone.py`：实际执行的 scratch 错误变体。
- `full-verification.json`：对已有完成回执、timing、原日志和13项新测试输出的核验；没有重复 full。
- `consumer-binding.json`：四个输入、两份输出和准备来源的摘要核验。
- `finalize-review.py`：本报告的只读身份/证据绑定与生成逻辑。

当前合同、两份生产 Skill、新增四个测试/fixture 文件全文已读；聚合注册和预注册身份改动的完整 hunks 已读。原 host/IMAP probe 在设计审查时已读源码和结果。消费者 task/observations/Markdown 全文及 JSON 关键字段和完整 IMAP 判读已读。full 完成回执与 timing 完整解析，原日志做完整 byte/hash 核验并检查总结果、新测试与失败标记；未逐项重新审查与本次无关的102组内部实现。辅助 reviewer 解析全部归档并校验40项原字节，但没有逐行语义审查每个历史日志。

规范依据已独立读取 Linux 6.12 fault-injection 的 fail-nth 激活语义、RFC9051 §2.3.3/§6.4.4，以及 Python3.12 imaplib 的 stream/UID/response/FETCH 定义；具体 URL、版本及读取范围列在 JSON 中。

## 限制与交付边界

没有设备/HIL、实际 RTOS/故障恢复时延、SLA、真实邮箱/TLS/认证或服务端无副作用资格。固定本地 IMAP peer 的内容预算检查不是所有协议响应的通用 wire-byte 限流器。消费者使用准备好的源方法任务；其无sender日级搜索列表来自fixture推导，不是新的真实邮箱命令。单次观察没有 native/A-B/Token/成本或泛化效果意义。

两个改动都是方法增强；受控坏变体不说明 ADK 已有运行态判定器存在漏洞。`large-refactor` 原预算只剩8字节余量，当前通过且未提高阈值。后续包装只可追加证据和 verification，并按约定做一次增量包装审查；本报告不替未来改动或未执行的发布步骤背书。
