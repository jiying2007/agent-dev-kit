# Skills execution development tasks

这 8 类是公开的 **development** 任务，不是 holdout，也不是模型执行记录。`suite.json` 仍标 `evaluation_status: not-measured`。每个目录含 `task.md`、可复制的 `initial/` 输入和独立验收者使用的 `case.json`。任务要求的文件是实际产物；验收不以路由命中、某句成功声明或文件名存在代替内容正确。

## 任务与验收

| Task ID | 初始输入与任务 | 确定性断言 | 已覆盖的错误产物 |
|---|---|---|---|
| `deadline-repair` | Python deadline 边界错误、原症状和正常路径测试；单项修复 | 授权条件从 `<=` 改为 `<`，其余源码/测试不变；0/99/100/101 ms 的结构化预期结果均正确 | 保留旧 bug；有正确预期结果也不能使错误源码通过 |
| `review-false-positive` | 实际 `is None` 分支与错误 R1 finding；仅核验该 finding | 原码/原 finding 字节不变；None/0/1 的完整结果、误报裁定、范围正确 | 错当 confirmed、要求改正确代码 |
| `goal-resume` | 旧 checkpoint 为 unknown、实际成功发布回执、已完成包 | 对账后补 index；保留包和回执；父 Goal 仍打开且只剩设备验收 | 过早关闭父 Goal；添加重放发布回执 |
| `kws-asset-reuse` | 已核验合成特征、非匹配资产、带摘要/profile 的清单 | 选用适配且摘要正确的已有特征；所有资产与清单保持字节；不声明板端实测 | 选择 stale 资产；只有 selection 自称成功但缺真实资产 |
| `crosscompile-applicability` | Buildroot Autotools infra、缺 aclocal log、Linux 与 MCU 能力 | 保留原失败与配置；定位 host Autotools；Linux perf 与 MCU DWT 分开且均未实测 | MCU 套用 perf；类型/字段/构建结果偏离均失败 |
| `targeted-document-edit` | 含 250 ms、250 mA、proposed/pending 与否定授权的 ADR | 唯一授权句改为 500 ms，其余完整字节相同 | 顺手改保护阈值、其他字段或状态 |
| `intent-distinction` | 一个已批准继续执行请求、一个尚缺目标平台的探索请求 | 明确请求直接继续；模糊请求只问改变实施路径的 target-platform | 把已批准工作退回 Explore 并重复确认 |
| `optional-availability-negation` | 安装清单、未安装/显式否定/已安装可选三个请求 | 缺失或被否定均不拟加载/安装；已安装且被允许才 eligible | 因为已安装而加载被否定 Skill；数字 0 冒充布尔 false |

所有任务同时验收整个 `work/` 文件集合；缺文件、额外文件、链接与特殊文件均不通过。JSON 比较检查完整结构和值，区分布尔与数字并拒绝重复键/NaN/过深或超大输入。文本修改验证整个文件与唯一替换的结果，保留区逐字比较。受限合同只接受本套规定的产物格式和修复跨度，不宣称覆盖所有语义等价的解法。

## 准备和独立验收

由 owner 把某个 `initial/` 的内容复制到新证据包的 `work/` 中，只把 `task.md` 和工作目录交给执行者。`case.json` 和原 `initial/` 留在执行者写权限之外；它们是公开开发答案，不应放进将来盲测执行者的上下文。运行前冻结任务、候选 Skill、输入摘要、权限、预算与验收版本；不要在看到结果后改答案。

执行完成后，由不同身份的验收者调用已有 eval 入口，例如：

```bash
PYTHONPATH=src python3 -m agent_dev_kit.cli eval grade-task \
  --case tests/fixtures/skill_execution_tasks/targeted-document-edit/case.json \
  --workspace /absolute/path/to/evidence-package \
  --output acceptance.json \
  --run-id development-1 --executor-id task-author --grader-id artifact-grader
```

`--workspace` 是完整证据包根；产物路径为 `work/...`，`--output` 必须位于包内且在 `work/` 外。调用生成 `acceptance.json` 和 `acceptance.json.checks.json`；后者记录实际验收项、状态、摘要和未验证边界，不复制产物正文。验收 JSON 使用与 `import-task` 共用的 `adk-task-acceptance/v1`，包含 `trust: caller-observed`、`evidence_scope: test-only`、`raw_content_stored: false`。身份不同由调用方声明，不是身份认证。

失败会保留全部验收项及可读取产物的摘要；不能只留下通过项。附加文件可能使 artifact-boundary 失败，即使其他内容检查全部通过。模块不执行候选 Python、命令、构建、测试或网络请求，也不解析任意自定义检查器；只支持完整 JSON 相等、原字节保持和唯一文本替换三种检查。

## 证据适用边界

`passed` 只表示本开发工件合同符合。最终文件集合不能证明中途未越权、未重复外部发布、未外传数据，也不能证明 Skill 已加载、测试真正运行或板端行为。真实过程必须独立保留 trace、权限事件、实际加载、usage 和原始产物；合成任务不得填 E2–E4 或声称真实成功率/Token/时延改善。导入与配对比较见 `docs/runbooks/task-evidence.md`。

测试入口沿用 `bash tests/test_skill_content.sh`，其中 `tests.test_skill_execution_tasks` 对每类都验正确产物、错误产物和未完成输入；另覆盖路径/链接/FIFO、JSON、越界、身份与命令拒绝。deadline 用例还对**仓库自带的已知 fixture**运行原症状 RED 和固定修复 GREEN；这证明测试例有效，不代表模型完成过该任务。

本套不能替代候选冻结后的独立 holdout。真正的模型基线/候选执行只能由用户允许的宿主运行，本仓库不创建新 runner、付费模型调用或定时任务。
