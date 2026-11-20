# ADK 最佳实践：少流程、真实证据、可恢复

本页只保留**跨任务适用的工作原则**。不再复制命令手册、完整 Workflow 阶段定义或历史版本演示；场景提示词见[Practice Cookbook](best-practices-cookbook.md)，CLI 参数见[命令参考](commands.md)。

## 按改动风险选择最小路径

| 任务 | 做什么 | 不做什么 |
| --- | --- | --- |
| 单点修复、明确的文档编辑 | 限定修改范围，定向验证并复核 diff | 不强制开 Goal、SDD 文档或多轮访谈 |
| 不明根因的 Bug | 复现、记录假设、单变量实验、修复与回归 | 不靠重跑至绿、不顺手重构 |
| API、协议、状态机、跨仓变更 | 复用权威规格，记录行为增删改、正负验收、双向测试 | 不复制第二套 Spec 或并行路由 |
| 长任务 / Goal | 保留真正完成的检查点、证据指针和可恢复下一动作 | 不把 CI 查询、文档整理当实际开发推进 |
| 发布 / 设备操作 | 明确权限、不可变源码、目标凭据、回滚与现场证据 | 不拿源码通过冒充 Runtime/产品放行 |

完整的 [SDD 最小路径](runbooks/spec-driven-delivery.md) 和 [Workflow 适用范围](workflows.md) 是具体做法，不应按本页再制造一套阶段状态机。

## 验证按层级升级

- **普通源码小改**：优先定向测试，并检查实际变更范围；风险上升时扩到回归。
- **ADK 本仓受保护变更**：运行实际环境中的 `bash scripts/devkit.sh validate --strict`、`bash tests/run_all.sh --quick`；合并前以 **最终 HEAD** 的完整 CI、独立审查和保护规则为准。
- **目标运行时**：单独确认安装、发现、加载、触发、工具副作用和错误恢复；仅有文件或 matcher 命中不能证明原生可用。
- **模型效果与成本**：记录同任务、同模型/环境、预注册验收与真实 provider usage。缺失计 `not-measured`，不得填充零。
- **产品与现场**：必须由消费方自己的受信验收与现场回执判定，不继承 ADK Release 状态。

## 版本、撤销与安全

变更前记录精确源码与测试基线；在受保护 PR 中使用受控 SemVer 更新，**不能**把旧示例版本当作当前升级目标。禁止强推、改动已发布的 tag、跳过失败门禁；失败时保留原始日志、影响范围与回滚动作。备份/恢复必须审查受管路径与 receipt，参见[维护与发布](runbooks/workspace-maintenance-guide.md)。

外部 Skill、脚本、MCP、参考仓默认视为不受信来源；来源审查、权限和真实可执行结果分开核实。优先使用已有 Asset、Runbook 和测试，不因每次优化新建同义 Skill、治理引擎或定时扫描。

## 文档维护的唯一事实源

- `manifest.json`：Agent、Skill、Profile、Workflow 及当前源码版本
- `docs/commands.md`：CLI 命令参数
- `docs/workflows.md`：Workflow 与普通任务场景的关系
- `docs/changes/`：变更证据和历史快照，不是普通用户首次上手必读
- GitHub exact-SHA CI、不可变 Release、消费方凭据：各自证明不同范围

维护时尽量**修改权威文档并链接它**，不要在多个页面重新粘贴同一套执行步骤。历史实验附件不因文件相同就擅自删除，清理前需核对原始证据引用。
