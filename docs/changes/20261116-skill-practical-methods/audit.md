# 审计范围与执行层次

## 覆盖

继承上一轮逐项阅读与摘要绑定的 65 个注册 Skill、53 个直接参考文件，共 118 路径：@docs/changes/20261116-skill-execution-fidelity/audit.md。新一轮 general 与 practical 审计先复读各自任务域，external 从一手具体 Skill 和官方文档寻找当前缺口；没有将改动数量当作质量指标。

本轮深入修改 7 个现有 Skill：`adk-code-review-loop`、`adk-context-engineering`、`adk-context-compress-handoff`、`adk-performance-profiling-embedded`、`adk-cmake-cross-build`、`adk-protocol-stack-integration`、optional `adk-test-flakiness-triage`。另外修正已有 ADC 示例并接入既有真实命令测试入口。其余 58 个 Skill 本轮不作无依据改写；身份、安装范围、权限与宿主运行时保持。

## 可证伪的发现

| 发现 | 基线证据 | 修复后的验收对象 |
|---|---|---|
| Review 目标漏采 | staged 阳性；unstaged、clean committed branch、同文件 staged/unstaged 三组漏 patch | 实际导出模板执行结果、diff 内容、index/源文件不变 |
| 默认交接隐含源仓依赖 | 6 profiles × 2 targets 的渲染资产无源仓 schema/template；两 target 的 core 完整 export 核对缺失 | 正文默认字段及条件性辅助路径；没有把 schema 校验伪装为执行成功 |
| ADC 中间乘法溢出 | 24-bit 满量程/钳位得 -28，INT_MAX 满量程得 0；UBSan 真实报警 | host 编译运行、边界不变量、受支持 UBSan；不推断板端资格 |
| CMake 配置身份脱节 | preset 的 out/demo-release 与后续 build/demo 不同 | 真实 configure/build/CTest/artifact；本机缺工具与 CI 执行分开 |
| 堆峰值工具选错 | 正文“堆用 memcheck”；两个逻辑负载末端均 0，峰值不同 | 工具与指标映射、插桩扰动；未运行 Valgrind |
| flaky 顺序污染 | victim 新进程 8/8 通过，同进程 polluter→victim 失败，反序通过 | 条件性原顺序/seed/worker/进程对照；没有稳定率推断 |
| 局部 timeout 不保证总时限 | 分段模型 2600>2000 ms；次数模型 3400>2000 ms；三层三尝试为 27 次 | 总剩余时限、退避计时、已有重试责任；没有网络故障注入 |

## 证据和角色

基线原始研究、可重现脚本、JSON 和独立设计预审放在 `evidence/general`、`evidence/practical`、`evidence/research`，索引为 `evidence/research-input-index.json`。模型反例只有方法意义；脚本执行、源码回归、独立审查、平台 CI 与真实模型评测不混计。

general 实现 Review/context；practical 实现 ADC/性能/CMake；root 实现 protocol/flaky 并集成。external 不编辑源码，独立做设计预审、方法早审和最终 Spec/Quality。早审两条非阻断措辞建议已采纳：业务延期不延长已耗尽操作期限；测试隔离按需执行并保留原失败状态。

最终源码、完整回归、预算和独立审查以本 change 的 `verification.md`、`review-findings.md` 与摘要绑定 `review-evidence.json` 为准，不提前将进行中的工作记为已完成。
