# 全量 Skill 审查与五项失败路径

基线为 ADK `v11.3.9` / `80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b`。本轮重新分组全文读取，不沿用上一轮逐项结论。整合器按固定 Git commit 重新读取所有资产 bytes，与各组文件、blob、SHA256 和决定逐项对账；实现期间工作区的变化不参与基线统计。

## 覆盖与决定

| 组 | Skills | 文件 | UTF-8/资产字节 | KEEP | ENHANCE | OBSERVE |
|---|---:|---:|---:|---:|---:|---:|
| Core | 34 | 93 | 231726 | 30 | 2 | 2 |
| Embedded | 22 | 45 | 123379 | 20 | 1 | 1 |
| Optional | 9 | 15 | 66983 | 7 | 2 | 0 |
| 总计 | 65 | 153 | 422088 | 57 | 5 | 3 |

无漏项、重复路径或重复 Skill 决定。原始阅读范围、逐项理由和限制见 `evidence/{core,embedded,optional}-audit.json`；精确 population、来源去重与再次摘要验证见 `evidence/portfolio-audit.json`。阅读是审计者的实际工作声明；整合器复核了字节和清单，不能机械重放“已经理解每一行”。KEEP 表示目前已有方法覆盖所查风险，不代表获得本轮效果提升或所有工作负载认证。

## 纳入修复的反例

| ID | 实际缺口 | 最小改动 | 验证与边界 |
|---|---|---|---|
| F1 | 7 条发布扫描中，6 条将匹配行的合成 secret 输出到 stdout | 所有初筛只列候选路径；去掉 license 的前 20 行截断；保留 exit 1/2 | 执行真实发布命令，检查候选完整性、sentinel、无匹配/读错误、hidden/ignored 与 `.git`；不证明敏感文件名脱敏 |
| F2 | 采样子进程返回 130/143 或自发 SIGINT/SIGTERM 后仍继续调用，最终被折成普通失败 1 | 当前日志和 TSV 落盘后按原码停止 | 真实子进程、调用次数/下一目录/原状态；正常 0/1/9/124 与采集错误控制；不证明父 shell/进程组取消 |
| F3 | 旧 CMake binaryDir 从 A 改 B 后 cache 显示 B，实际编译仍 A；强制重编译也如此 | 复用前核真实身份；变化/无法证明时选新任务目录与匹配 preset，保留旧证据 | CMake/Ninja/GCC 主机物理反例、同身份增量和新目录控制；另用新上下文消费者验证方法采用，不冒充硬件 ABI 或模型 A/B |
| F4 | 一律 `additionalProperties:false` 使 allOf 合法扩展被拒；Draft7 又会忽略 `unevaluatedProperties` | 明确消费者 dialect/validator/子集；同层闭合、现代组合边界或旧方言同层展开 | 真实 jsonschema validator 执行发布示例与反例，保留 required/type/enum/未知字段拒绝；不推断其他窄子集支持 |
| F5 | 空 Completion Review 的 5 行默认 pass，Evidence 为空，并随真实导出复制 | 默认 `not-run`，有逐行证据后再裁决 | 解析 claude-code/opencode 实际导出表格及证据单元；不新增 Gate 或工作流状态 |

原始诊断探针与实施前后执行回执保持分开。F3 的确定性控制在旧版和新版均通过，证明物理行为与可行路径；它们不是模型 RED/GREEN。F4 新增示例前的“缺示例”测试失败也不替代原始组合语义反例。所有实际失败、测试收集器修正和预算拦截记录在 `negative-results.md` 及原始回执。

## 保持观察的三项

- `adk-production-field-readiness` 的 human-active 与 wall-time 含义：缺真实 producer/单人或累计多人定义，不能仅凭词义改约束。
- `adk-worktree-isolation` 的旧任务模板默认低风险：当前实际链接消费路径不同，尚未证明旧模板是默认入口，不扩大改动。
- Embedded diagnostic harness 的 invocation 关联：需要真实 adapter/schema/replay 才能判断缺陷；相邻 HIL 方法已有 freshness/identity 边界，不凭审计新增通用 run-id。

这些是明确保留待证伪问题，不作为已修复缺陷或新认证。

## 集成边界

沿用现有资产结构、测试入口、8 个 profile 阈值和授权。没有增加 Skill、产品 registry、SDK guard、安装器、Gate、外部依赖或自动巡检。新说明放回既有 Skill/reference；因预算不足，对现有重复说明做等义精简，保留原能力、安全边界及真实执行例。

`~/codex` 缺失时的 source-only 例外已由用户授权；Knowledge Provider、Execution Policy 和 native runtime 证据仍 unavailable/not-run。主机构建、静态导出、内部消费者任务不等于 M5、HIL、现场资格，也不构成 token、费用或稳定胜率测量。
