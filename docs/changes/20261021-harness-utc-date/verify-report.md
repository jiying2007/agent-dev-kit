# 最终本地验证

版本身份：8.0.37。实现基于 `42ae95d146ceb441ff91ea33dbbed581c33de305`；本报告是工作树源码候选的实际本地验证，不代表后续受保护主线或产品资格。

| 检查 | 实际结果 | 原始证据 |
| --- | --- | --- |
| UTC 确定性 red | 2 方法、3 失败子项，exit 1 | `evidence/utc-regression-red-*` |
| 审核证据回归 | 45/45，exit 0 | `evidence/utc-review-regression-green-*` |
| 历史审核兼容性 | ADK 5/5，Root 3/3 | `evidence/archive-compatibility.json` |
| 独立 Harness Spec/Quality | 实际逐内容审核 PASS，60 原来源加 2 UTC 测试 | `evidence/independent-harness-spec/`、`independent-harness-quality/` |
| 首次 record 组装 | finding ID 大写被正确拒绝 | `evidence/assembly-red/` |
| 新 record validator | PASS；62 source + 2 evidence | `.adk/reviews/harness-source-20261021.json` |
| 当前日 Harness gate | 02:02:46.518556Z，exit 0；6 PASS + 1 N/A | `evidence/harness-current-gate-green-*` |
| Harness 定向回归 | 02:02:48.119734Z，exit 0 | `evidence/harness-renewal-green-*` |
| 最终独立整合审核 | 02:07:28Z，Spec/Quality PASS，无开放源码 blocker/major | `evidence/integration-review.json` |
| 完整回归 | 02:02:52.041383Z–02:09:22.356229Z；101/101，exit 0 | `evidence/full-receipt.json`、`full-stdout.txt`、`full-stderr.txt`、`full-timing.json` |

完整回归实际运行 390.315 秒，Python 3.12.14，运行记录的 `allow_network=false`；该结果不作为 provider 运行证据。stdout 为 3138 字节，SHA-256 `9f7a87cd72584ab6c53ea102ca7795538c04eaf644ab46dbd80c521b469bee69`；stderr 为零字节。原先 99/101 的全量失败、首次中断与所有 red 仍保留，最新成功不改写历史。

新 canonical record SHA-256 为 `cf140e4be5f0508f5ee2f731aebaebc8fff1c17a83cd0e889e535de427cde1dc`。七个 metadata pointer 已通过实际检查；旧 October 20 record、policy、授权原件、三份共享 validator 全部未改。两个 finding ID 的小写映射只符合现有 schema，语义与审核原件一致。

最终整合审核快照之后仅补充本地执行原件、任务进度、验证报告和已接受的时间说明，并移除三个完全相同的中间目录副本；产品源码、测试、新 canonical record 和其两个证据均未变。三份含原生尾随空格的失败 stderr 改为无损字节封装，解码后逐字节与原件一致。Python 3.8/3.11 实机、受保护 PR/main CI、不可变 Release 与 Root 精确晋级以各自后续回执为准。

原始报告保留捕获时的 scratch 相对路径。两类独立报告目录名称原样保留；测试捕获输出从 `stdout.log`/`stderr.log` 以相同字节保存为对应 `*-stdout.txt`/`*-stderr.txt`，避免 Git 的 `.log` 排除规则。三份含原生尾随空格的失败输出改为 `*-stderr.bytes.json`，包含完整 Base64 数据、原始字节数及摘要；解码后与原始 receipt 的 SHA-256 一致，不裁剪原文或放宽空白门禁。`field_evidence_status` 始终为 `not-verified`；本地回归与源码审核不生成 Native/G22/LTA/M5 终态证据。
