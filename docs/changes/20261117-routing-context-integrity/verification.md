# 11.3.15 源码审查与验证

## 精确范围

本记录针对基线 `6d902f721f560f02883516e809fbd93a326405b6` 到产品源码
`713d0d3a85c74bd9fe4b27a23c8dc8b2a066565a`，产品树为
`1f9c586dadb20d6195263cd305efa9e5080291e2`。完整原始差异位于
`evidence/original.patch`，SHA-256 为
`1b1b1c4d33ed504a36e7796c41421fff7939270a3e8f0b2dc2fbce5f752ace57`。
后续新增审查与验证记录是证据包装，不改变产品源码、schema、Skills或测试。
`.gitattributes`仅为4个保留原字节的失败日志/旧patch增加具体路径的whitespace
属性，源码格式检查保持；包装后的cached diff check已通过。发布、Root 接入
仍须各自的受保护主线 CI 与不可变制品证据，不能由本地测试代替。

全部65个 Skill 与54个直接参考有逐项审查记录；独立检查将119份原始
文件的路径、字节数和SHA-256与基线Git对象逐一核对。当前仅4个Skill
正文发生修改，身份、直接参考集合与参考内容保持不变。外部检索深入核验
7个官方或原作者来源的固定版本，采用和保留理由见 `source-review.md`。

## 已实现的改进

- 四处原有有界LRU按读取的不可变内容复用解析；phase/relationship的
  schema同时参与身份，摘要取自实际解析字节。同大小、恢复mtime的变更
  仍重新校验，读取及编码失败不再被旧缓存掩盖。
- 当前明确动作优先于旁边的主题；被否定长动作中的短别名不能复活。
  worktree修饰语、ADR写作、自然RTOS SPI/DMA驱动实现均有成对控制。
  说明/审查对象不被当成写请求，先…再…后续肯定动作仍能生效。
- 上下文只有在同来源、同内容且完整正文仍有效时才能去重；压缩导致正文
  丢失或来源改变时，按当前目标与权限恢复仍需的Skill及引用。
- 效果记录严格区分布尔和数值，拒绝NaN、Infinity、超大整数转换及合计
  溢出；合法零值、实际错误记录与原有缺失成本语义保持。

## 实际验证

| 验证 | 实际结果与范围 |
| --- | --- |
| 最终完整源码回归 | **102/102组，退出0**；2026-11-17 12:26:52–12:32:52 UTC，359.637秒 |
| 执行环境 | 同一产品提交的洁净detached worktree；外部既有Python 3.12.14工具环境，无模型或设备调用 |
| 输入一致性 | **1082份**运行相关tracked文件执行前后摘要一致；排除累计change/report/result证据，包含src、tools、scripts、tests、schema和Skills |
| 原固定确定性路由 | **60/60**；原任务字节、期望与grader未修改。默认30场景亦通过既有回归 |
| 实施定向回归 | **59个测试通过**，包含顺序正反控制；与完整回归有重叠，不累加为独立样本 |
| 独立路由观察 | 原30个边界 **30/30**，已识别顺序5正7反 **12/12**；最终trigger matrix 32 tests通过 |
| 缓存与输入观察 | 独立读取后内容变更探针确认摘要和解析同字节；原6项数值探针全部符合预期 |
| 上下文消费观察 | 最小输入的完整正文复用、正文丢失恢复、来源改变重核3个情境；是有限消费观察，不是模型A/B |
| 原8个Profile阈值 | **8/8通过**；阈值文件与基线字节完全相同 |
| 模块预算 | 最终内核**28930B**，原上限仍为30000B，无新增support模块或预算例外 |
| 严格与发布前检查 | 最终源码strict、release check、Ruff、format均退出0 |
| 其余质量检查 | 本轮mypy、ShellCheck、pip-audit实际退出0；依赖审计返回No known vulnerabilities found。工具、范围、时间、日志摘要均保留；后续路由修复没有改这些依赖或Shell输入 |

`evidence/final/integration-summary.json`、`full-regression.log`、`full-timing.json`
以及前后源文件清单保留完整本地结果。`evidence/quality/`保留逐项原始质量
命令、退出码、工具版本与时间。`evidence/observation-index.json`列出封存
观察的字节与摘要；独立最终裁决另由reviewer写入，不由实施者自签。

## 开销与体积：只报告实际观察

相同60场景加20次phase和10次lifecycle解析的三轮本地负载，基线中位数
**73.010ms**，最终洁净执行**87.462ms**（高约19.8%）。同一候选在此前
源码根执行曾为**72.197ms**；这些少量观测和不同checkout条件没有隔离
环境影响，不能据此确定因果加速或回归。所有原性能预算仍通过，不以重跑
选择较好数字；原始各轮与条件见 `evidence/final/benchmark-comparison.json`。

四个修改的Skill入口文件合计17884B→17467B，减少**417B**，其中三个context
入口合计减少400B。这是源文件体积变化，未测量provider Token、费用或
真实任务端到端时延，不能换算成这些收益。

## 原始失败、审查修复与限制

独立审查发现IR-1数值聚合溢出、IR-2带修饰语的局部否定、IR-3解释对象
与后续顺序动作三项实质问题，均保留RED并在最终源码上fresh复验为fixed。
首次冻结还遗漏未执行对照计划的candidate版本元数据；仅同步planned
release，保留not-measured、no-model-runs、空results及原train/holdout。

两次不完整本地执行均保留：第一次已出现版本元数据失败并因顺序回归被
中止；第二次安全fallback把源码根内工具venv纳入扫描而失败。后者通过
同一提交的洁净源码目录、外部原工具环境验证，无scanner或测试放宽。
详细原因与原始记录见 `negative-results.md`、`evidence/first-incomplete-run/`
和 `evidence/source-root-environment-failure/`。

保留SK-05词法覆盖限制：`继续执行已有计划，不要重新拆解任务`在基线
返回abstain，既有`按现有计划继续执行`可命中。本轮没有声称任意自然语言
表达完备。历史hosted ADC/CMake超时根因仍未确认；本轮实际本地通过
不构成根治证据。未安装live runtime，未执行模型对照、SSH/设备/HIL，
未取得native宿主、Software M5或现场资格。
