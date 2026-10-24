# F1 发布 bundle 完整性：独立只读复审

**结论：本范围 Spec PASS、Quality PASS，当前未解决的 F1 阻塞项为 0。** 初版实现上发现的三个 P2 均有原始公开入口 RED、修复后的同探针 GREEN，以及最终提交的逐文件绑定。本结论不代替完整回归、精确提交的远端 CI、签名或发布授权。

审核者：`/root/release_governance_audit`。审核期间未修改 ADK 的 F1 源码或测试，未写远端、提交、打标签或发布。F2 subprocess/smoke 由本审核者实现，明确排除在本独立行为结论外；该部分的独立审核由 `/root/root_code_audit` 负责。

## 精确对象与时间

| 对象 | 精确值 |
| --- | --- |
| 原基线 | `415590db44e88979185efb850e2339a3f95411ef` |
| 保留三个原始 RED 的初版 | `fa0bf9691e24113a0064cbe4c7f6f62ca6e1bb47` |
| 修复后实际行为测试所对应提交 | `775352c86a5f67f38b6d3650f8b933e832c7f49c` |
| 最终审核、证据打包提交 | `3f0f0599de49140ade2225540dd44f2fb42030ad` |
| 最终 tree | `a49a55acb74e143326073b4e0205886ad7219585` |
| 最终源码执行区间，UTC | `2026-10-24 16:31:35.772052` 至 `16:40:35.232937` |
| 10 份源码/测试集合摘要 | `159eb3966fea67fd48f6409b45c8e1444a65a2fc53496114f3f5d1f779fe3d6e` |
| 完整 `415590..3f0f059` binary patch 摘要 | `8caf8c7e7fa8ce68dc981f4aadbee5e2852138e03f8d5caf0ec89a9858616c35` |

实际核对了 10 份源码/测试和 4 份当前合同文档：工作区字节、775352 Git blob、3f0f059 Git blob 全部相同。最后一次提交的 9 个变更仅涉及实现验证文档和原始失败输出的无损容器，没有改动生产代码、测试或当前 requirements/design/commands/CHANGELOG。每次实际执行均记录开始/结束时间、命令、退出码、stdout/stderr 摘要以及前后源码指纹。原执行时间和初版 FAIL 未因最终提交产生而回写。

完整机器记录为 [review-summary.json](sandbox:/workspace/scratch/712af632e2a5/apply20261024/review-f1/review-summary.json)，最终 Git 绑定为 [binding-3f0f059.json](sandbox:/workspace/scratch/712af632e2a5/apply20261024/review-f1/binding-3f0f059.json)。全量原始 patch 位于 [original-implementation-415590-to-3f0f059.patch](sandbox:/workspace/scratch/712af632e2a5/apply20261024/review-f1/original-implementation-415590-to-3f0f059.patch)；其中也包含 F2 和版本同步，不能据此把本审核的独立范围扩大到 F2。

## 三个已修复的 P2

| 编号 | 初版真实观察 | 最终修复与独立结果 |
| --- | --- | --- |
| F1-REVIEW-01 | 原 manifest/target schema 离线 guard 漏掉 Native receipt schema。合法 runtime 合同经公开 validator 进入第三份 schema 的外部引用解析，随后才失败。探针在 urlopen 边界拦截，实际网络请求为 0。 | 同一离线 guard 覆盖固定 Native receipt schema；存在时先检查，拒绝外部 `$ref`、`$dynamicRef`、`$recursiveRef` 和嵌套引用作用域。原探针在 Python 3.12、3.8 均在解析前拒绝，外部引用调用为 0。 |
| F1-REVIEW-02 | 包内 schema 可放宽 support directory，导致 reviewer 自有源外临时目录先被 rglob 枚举，随后才由逐文件 containment 拒绝。观察仅证明元数据遍历，没有声称读取外部正文。 | support root 在 exists/rglob/read 前经原 ensure_within owner 检查，仍用原始 Path 做 symlink 拒绝。两版本原探针均无源外遍历；实现回归另直接计数 exists/rglob，均为 0。 |
| F1-REVIEW-03 | 原始完整 receipt schema、合法三阶段 receipt 和归档 registry 能把宿主 `/usr/bin/true` 及其真实 SHA 送到 subprocess.run。所有执行均被探针拦截，没有实际执行宿主程序或归档代码。 | release 公共入口固定 `allow_native_verifier=False`，沿私有历史 renderer/loader 传递，runtime 分支在构造 managed verifier 前拒绝。两版本原探针均观察到宿主 subprocess 调用为 0；没有把未验证 runtime 降为 static 后放行。 |

原始 FAIL 和原始效果记录保留在 [findings-initial.json](sandbox:/workspace/scratch/712af632e2a5/apply20261024/review-f1/findings-initial.json) 与 [findings-initial.md](sandbox:/workspace/scratch/712af632e2a5/apply20261024/review-f1/findings-initial.md)。所有恶意输入均为仓外临时归档，网络与宿主执行在效果边界被拦截；正式 v8.0.39 包从未被修改。

## Spec 与调用链审查

归档验证继续先检查 release manifest、SBOM、内外 source manifest、source 文件数和 source digest。新的 bundle 校验从同一份不可变 raw bytes 第二次有界解析 source，私有临时根为 0700；不重新打开可被替换的归档路径，不导入包内 Python。实际 archive-resource 用例也覆盖路径替换后仍使用原捕获快照的行为。

期望 bundle 来自当前已加载的可信 renderer。核对每个 direct target 的数量、完整文件集合、内容摘要、模式及真实 export manifest 字节；仅重算包内 export manifest 不能授权修改后的 Skill。已存在的目录条目必须属于期望文件的父目录且模式为 0755；省略冗余目录标记仍被允许。`compiler.export_manifest` 提取的是原内联清单构造，普通 export 与 validator 使用同一字段定义和序列化顺序。

沿真实消费者核对了三处 schema：Manifest 的 `manifests/manifest.schema.json`、target loader 的 `manifests/target-contract.schema.json`、Native receipt 的 `schemas/native-target-conformance-receipt-v2.schema.json`。release 必检第一处固定 schema，因此 Manifest 的嵌套 source fallback 在此路径不可达。registry 使用既有结构验证，没有发现另一处可绕过 guard 的 schema 解析入口。JSON Schema 的格式检查没有授权外部网络访问。

Native 的新许可参数仅在私有历史 renderer/loader 中增加，默认 True。普通 `load_target_contract` 保持原调用；installation inventory 也不传入新的拒绝参数。公开 release validator 没有可供调用方绕过的执行开关，并在 managed verifier builder 之前失败关闭。本地自动注入 managed verifier、精确注册 receipt、错误 scope/binary/bundle/signature、安装恢复与 receipt 权威的既有行为均由实际正负控制复验。

归档内部的 source inventory 仍是内容一致性证明，来源认证继续属于完整归档签名和受保护发布链。本变更没有把包内自报 registry、digest 或 `release_eligible` 变成外部授权。

## 资源预算与历史兼容

release 显式创建共享 RenderBudget，沿现有 archive owner 的默认上限约束输出：总字节 128 MiB、单文件 32 MiB、文件数 8192、路径 UTF-8 字节 4096。预算跨资产、全部 targets 和 export manifest 累计。YAML 输出在编码期间写入有界缓冲，support 先查大小再分块读；没有先保存整个放大结果再检查。

实际通过的 ReleaseInventoryTest 包含：深层 JSON 转 YAML 导致单文件放大、跨资产/targets 总量放大、80 个别名复用同源导致文件数放大、重复 48 KiB support、export manifest 自身超过文件预算，以及精确字节/文件/路径边界和减 1 反例。测试用较小预算复现真实放大行为，没有尝试耗尽宿主内存。字节与数量限额不代替操作系统 CPU/内存隔离。

对已下载的正式 v8.0.39，重新核对完整 SHA256 `680ab5bbf4340c5ae75e1e8441dc3531a50795d1c0d8e395a84448ba4429b487`，canonical 与发布前断言均 PASS。六种仅在临时副本施加的变体，在 source 文件字节不变、外层 checksum 已重算的前提下，均被两个入口拒绝：修改 Skill、删除全部 259 个 bundle 成员、修改 Skill 并重算 export manifest、模式漂移、删 target 并缩减自报 target 清单、额外未归属目录。

另一个独立探针把 target owner 的时钟设为 `2027-01-12`：同一正式包的 canonical 返回合同逐字段不变；同一 source 的 claude-code、opencode 新准入都返回 `target_contract_stale`。历史重建没有续期新准入。本审核未构建或发布正式 v8.0.40。

## 实际执行摘要

下表的时间是实际记录值；完整 argv、UTC 时间、前后指纹和原始输出均在 review-summary.json 对应 execution 记录中。

| 执行范围 | 实际结果 |
| --- | --- |
| 三个原始公开入口探针，Python 3.12 | 3/3 PASS；0.268、0.315、0.315 秒；外部请求/遍历/程序调用分别为 0 |
| 同三个原始探针，真实 CPython 3.8.20 | 3/3 PASS；0.566、0.667、0.569 秒；对应外部效果为 0 |
| `tests/test_release_manifest_contract.sh` | 22 archive + 4 CI authority + 31 integrity + 1 rehearsal，全部 PASS；50.742 秒 |
| 正式 v8.0.39 和六种变体，canonical + 发布前断言 | 全部符合预期；15.762 秒 |
| 正式包历史时钟与两项新准入 | PASS；2.320 秒 |
| 本地 managed Native、export、安装升级、receipt authority | 26/26 PASS；测试 7.226 秒，记录总耗时 7.439 秒；采用排他唯一 label 的重跑记录 |
| strict JSON 原有回归 | 14/14 PASS；记录总耗时 0.371 秒 |
| 默认 Ruff；distribution 的 CI 严格选择 | 均 exit 0；0.032、0.033 秒 |
| Mypy 五个生产模块 | exit 0，no issues；1.067 秒 |
| 实际模块预算脚本 | PASS；2.421 秒 |
| F1 范围 `git diff --check` | exit 0；0.008 秒 |
| 最终完整 patch 与实际 `scripts/check-format.sh` | 均 exit 0；0.016、0.316 秒 |
| 另一独立 reviewer 的精确 775352 / Python 3.8 补验 | Inventory 20/20，2.055 秒；本地 managed Native 两项正控制 2/2，0.084 秒；已实际读取原始记录并核对 source 前后相同 |

3.8 补充记录为 [executions-post-f1-775352c86a5f.json](sandbox:/workspace/scratch/712af632e2a5/apply20261024/review-f2/executions-post-f1-775352c86a5f.json)，其真实执行者为 `/root/root_code_audit`，不能归为本审核者执行。该记录还包含 F2 复验，但本 F1 结论只引用上述 Inventory 与 managed Native 控制。

## 证据异常与保留方式

第一次完整 patch 格式检查在 775352 上确实 exit 2，原因是原 F2 unittest 失败输出保留了一个行尾空格。没有把此结果当作 CI PASS，也没有删除或 trim 原始失败正文。最终提交将日志无损封装为 JSON/base64；本审核独立解码并与 fa0 原 Git blob 比对，4646 字节全部相同，原始 SHA256 为 `46f04ed1e3214d41a608577267c9bd6f56f0860b4c605ee22ff916547d654acb`。原 FAIL 记录保留，最终完整格式检查实际 PASS。

归档核验另发现第一次 `local-native-install-final.stderr` 的当前文件长度/摘要与其已写记录不一致。原因未定，不能作为可核验 PASS；原 JSON 与当前 raw 均保留，未修补记录中的摘要。将 recorder 改为排他创建唯一 label 后，以 `local-native-install-retained-1641` 重跑相同 26 例；新的 stdout/stderr 长度和 SHA 均与记录一致。上表与正式 verdict 只使用新的可核验记录。

其余所有被计入的执行记录都已重新验证原始输出 SHA。高置信度敏感信息扫描未发现 token、私钥或真实 Authorization；探针只使用测试身份、公开源码和 reviewer 自有临时路径。来源绑定不改写原 RED、审核时间或先前失败的事实。

## 仍由集成阶段完成的事项

本报告不宣称完整 ADK/Root 全量回归、精确远端 CI、最终合并、签名和 immutable 发布已经完成；这些由主 Agent 统一收口。没有真实 Native runtime、G22、LTA、现场或 Product M5 资格升级。当前公开 release validator 明确拒绝缺少独立可信执行授权的 runtime conformance 归档；未来若支持这类归档，需要另行建立可信上下文，不能借当前接口放宽。
