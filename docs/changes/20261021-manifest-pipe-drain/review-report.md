# 独立审核记录

作者为 `ai/root`（实际 agent `/root`）。本报告转录实际独立审核结果，源码绑定见 `evidence/reviewed-source.json`；不是预先生成的批准，也不是 Native/产品终态审核。

| 审核 | Reviewer / 实际 agent | 实际完成 UTC | 结论 |
|---|---|---|---|
| Spec | `ai/root/external_methods` / `/root/external_methods` | 2026-10-21T01:31:25.488033Z | PASS |
| Quality | `ai/root/native_evidence_audit` / `/root/native_evidence_audit` | 2026-10-21T01:31:23.422755Z | PASS |

上表为首次源码 PASS。后续 NUL 边界补证实际运行于 01:32:57.868762Z 至 01:32:58.375918Z，最终补充确认时间为 01:33:32Z；不归入较早的首次 PASS 时点。最终整合审核在 02:07:28Z 完成，Spec/Quality 均 PASS，原件见相邻 UTC 变更的 `evidence/integration-review.json`。其 19 文件历史快照保持原样，后续任务进度与交付报告另列。

两位 reviewer 均未实现、修改或提交本轮源码。Spec 仅阅读；Quality 独立运行了 manifest contract（十二个既有和八个新增 Python 测试）、runtime boundary 与 manifest consumer boundary 三项脚本，均实际 exit 0。其逐字节源快照及运行原件见 `evidence/quality-receipt.json`，各 shell 独立语法检查见 `evidence/quality-syntax-final-receipt.json`。旧 syntax receipt 的多参数 `bash -n` 只代表首文件，保留为历史但不作为七文件验收依据。Python 3.8 grammar 检查不冒充 Python 3.8 实机运行。

## HOLD → 修复 → PASS

初版遗漏 runtime boundary 的 handoff `must_not` 管道，两个 reviewer 均保持 HOLD。Quality 在真实大列表上复现 producer 2 / matcher 0；作者补齐第十一处生产 consumer，并在既有 runtime boundary 测试增加大列表正例及删除真实 guard 后恰好一个 failure 的负例。没有新增扫描排除、禁用 pipefail 或改 Python 错误处理。

Spec 逐字节复核 red/green stderr 与 receipt，确认失败和恢复都来自真实执行；保留 collector exit 与管道 exit 的区别、十八失败子项不全是 EPIPE、2026-10-20 历史根因仍未被重建等边界。

二次 NUL 边界调查未复现新增缺陷：合法 JSON 的无关 NUL guard 位于输出第 129 字节，其后为大尾部；真实 checker 成功，buffered/unbuffered 与普通/text grep 四组均记录 `[0,0,0]`。因此没有基于假设扩展修复范围。

## 审核绑定和后续门槛

- 基线：`42ae95d146ceb441ff91ea33dbbed581c33de305`。
- 已审 tracked diff：13821 字节，SHA-256 `c2ee63bcdf580c4e9275aecb72a9b174fe6b9589c3faab597e297cb35995faff`；未跟踪新增测试/文档另列入文件清单。
- 十九文件规范清单 SHA-256：`569b96b478cb4bed1ae28541a219a5a32a9eaf0be0ffeb3b97d2f5e10a3436e9`。规范化为按路径排序的 `{path,bytes,sha256}` JSON 数组，对象键排序、UTF-8、紧凑分隔符、无末尾换行。
- 审核时工作副本尚未提交。上述 PASS 只覆盖被冻结的源码变更；完整回归、受保护 CI、不可变 Release 和 Root 精确晋级仍各自等待实际完成。
- 原始 stdout/stderr 以 `evidence/*-stdout.txt`、`*-stderr.txt` 保存原字节；包含原生尾随空格的 red stderr 以 `*-stderr.bytes.json` 的 Base64 数据完整保存，解码后字节数及 SHA-256 与原 receipt 相同。receipt 中的 `stdout.log`/`stderr.log` 指捕获时原文件名。原始字节、空文件与摘要均保留，不以哈希替代原文。
