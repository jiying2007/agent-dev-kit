# 负结果与证据边界

- `knowledge/L2-domain/lessons.md` 在源仓不存在，不能补造历史经验；使用既有变更记录和新反例。
- Review 基线实际渲染的 Git 命令在 staged 阳性控制取得目标；working-tree、clean whole-branch、同文件 overlay 三组均 exit 0 却漏掉目标代码。这是模板证据范围缺陷，不能推断模型必然漏审。
- 新增 stat-only 反例证实 Git 2.52.0 的 diff 可刷新 index；只加 `--no-optional-locks` 的中间修复仍失败，原 `green-stat-only-final.json` 虽带 green 字样，实际 exit 1，保持失败记录。逐命令矩阵定位后用命令局部 `diff.autoRefreshIndex=false` 修复；该次修复匹配 `green-index-refresh.json`，不是较早的 `green-final.json`。随后 SOP 字段恢复另有新回执，最终源码以最新 source-freeze 和 full-receipt 为准。
- 首轮完整入口在冻结 `e0c3b97ef8382366939e3b5ed40263307604bd03` 上因既有 SOP 要求 `Snapshot ID:` 标识缺失失败（exit 1、27.405 秒）；原源码冻结、完整 patch、partial log/timing/receipt 原样保存在 `evidence/attempt1`。恢复原字段标识并保留所选目标语义，不改测试；后续完整验证必须绑定新冻结，旧 partial 结果不计完整 PASS。
- Context 源仓 schema/template 存在，但 6 profiles × 2 targets 的产物不包含它们；两个 core 完整 export 均确认路径缺失。默认流程不能假设消费端保留 ADK 源码。
- ADC 原 3 个测试通过；native C 在 24 位满量程/钳位返回 -28，INT_MAX 满量程返回 0；UBSan 报有符号溢出。期望来自端点不变量，未复用实现计算答案。
- CMake/Ninja 和 Valgrind 本地不可用。CMake binaryDir 反例当前只完成静态命令/配置核对；逻辑堆负载仅说明峰值与泄漏口径差异，不是 Massif/RSS 实测。
- 最终真实命令模块 26 项中，本地 21 项 PASS、5 个 CMake case 因缺工具明确 SKIP。模拟 GitHub Actions 缺工具环境的拒绝实验真实非零，只证明不允许 skip 变绿，不是 CI 实跑；真实 CMake/CTest 和 ADC CMake C11 接线仍须平台核验。ARM cross smoke 未执行。
- 同进程状态模型、整数假时钟和嵌套尝试模型只证明方法缺口，不计入 ADK agent A/B、Token/费用或真实设备结果。
- 普通 git fetch 已取得正确 PR HEAD 与文件树，但输出一条旧 object 无法读取警告；未擅自清理历史。新工作树的目标对象与源码摘要另行核验。
- 后续普通 main fetch 因本地旧 object 缺失未成功更新 remote-main；未把串行 shell 最后一个读命令的 exit 0 当 fetch 成功。使用 `fetch.negotiationAlgorithm=noop` 直接取得已知 `008c789312ed374f38d6d71a113f8fc91f89e63c` 后，确认其 tree 为 `72fa9e545532d184185ed7193cbd1f594a227d9f`，与本轮初始 HEAD 相同；没有清理或补造旧历史。
- 固定 GitHub blob 的 web open 有 DisabledError；读取相同固定 commit 的 GitHub contents 成功。没有把检索失败当作来源内容，采用依据仍来自原始文件及官方文档。
