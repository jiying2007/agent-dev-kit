# 证据来源与读取顺序

这些文件是本轮实际执行的记录，不是模型任务成功率或真实硬件资格。源码以 `source-freeze.json` 的文件摘要和 `original.patch` 绑定；首次中止版本的身份另存于 `source-freeze-interrupted.json`，不覆盖历史结果。

| 证据 | 含义与边界 |
|---|---|
| `portfolio-audit.json` | 65 个入口、53 个直接引用的基线完整读取与逐项决定；独立审查另核对 118 个 Git blob 内容摘要。 |
| `domain-baseline-red.json` / `domain-implementation-evidence.json` | 原 BSP 参数、C 接口边界的实际反例与改后真实 GNU make / C 编译验证；授权场景仅是静态语义审查。 |
| `implementation-red.json` / `implementation-green-initial.json` / `contract-reload-green.json` | 注册时间、观察窗口、验收组成与跨调用合同/schema 变化的实际 RED→GREEN；全部使用显式合成观测。 |
| `matcher-*.log` / `matcher-{red,identity-red}.json` | 原提升排除、直接名称拒绝、格式化名称与精确身份边界的失败和修复；两份 RED 原日志含行尾空格，改用 JSON 原样字符串保存并绑定 raw SHA-256，不修剪输出。`matcher-display-green.log` 文件名来自当时尝试，内容实际失败并含两个错误的测试模块名，不能按文件名认定通过。 |
| `preflight-final.log` | 修复版本身份 fixture 后的 59 项源前置检查；最终身份修复另由 `matcher-display-final-green.log` 和完整入口覆盖。 |
| `performance-{baseline,candidate,comparison}.json` | 同机同一 36 条合成观测的三次无 profiler 计时及三次 profiler 调用统计；结果不是模型延迟、Token 或费用。 |
| `benchmark_task_trials.py` | 实际计时脚本；以对应版本的 tests fixture 生成固定合成人口，通过 `PYTHONPATH=src:tests` 调用。输出位置是脚本所在目录，复跑应先复制到临时目录。 |
| `reproduce-domain-baseline.py` / `check_task_observations.py` | 历史基线反例脚本；读取旧 Git 文件或构造错误输入，不能冒充最终源码的正向验收。 |
| `profile-footprint.json` | 用现有计量器分别读取完整基线和候选 tree，八个原有 ratchet 不变；字节不是实测 Token。 |
| `questioning-partial-observation.json` | 精简前 Skill 的一次隔离部分回答观察；保留当时正文，原执行时间/hash 未采集，不能证明最终措辞。 |
| `questioning-revision-observation.json` | 上游修订后 Q11 失效、Q12 确认、Q14 暂缓的定性观察；原执行未采集时间/hash，后续完整正文核对一致，保存时间不冒充运行时间。 |
| `full-interrupted.log` / `full-interrupted-receipt.json` | 旧冻结全量入口主动中止：27 pass、0 fail、exit 130，无完整 timing，不计完整通过。 |

计时实验发生在提交冻结前的工作树，raw `head` 因此保留基线 SHA。`performance-comparison.json` 的候选文件摘要将实际实验代码绑定到后续冻结版本；不能把较早执行时间改写为在后续提交上运行。原始 profiler 二进制仅留本地，JSON 中的选定统计可读且受本轮摘要绑定。

最终完整入口、独立评审和证据索引在完成后单独追加。平台 CI、合并、tag、Release 属于后续平台观测，源码评审本身不证明这些动作已发生。
