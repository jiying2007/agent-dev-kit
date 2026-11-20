# 文档导航

本页是**入口索引**，不是第二套 Manifest、命令清单或版本状态。当前 Skill、Profile、Workflow 身份以仓库根目录的 `manifest.json` 为准；源码、Release、目标 Runtime 与产品资格分别核验。

| 读者 / 任务 | 唯一优先入口 | 主要内容 |
| --- | --- | --- |
| 首次使用 ADK | [快速入门](quick-start.md) | 最短上手、环境边界 |
| 日常执行 Skill | [按任务使用](usage.md) | 任务入口、已部署与未部署的区别 |
| 修改资产或管理安装 | [详细使用指南](adk-usage-guide.md) | Profile、导出、安装、回滚 |
| 查询 CLI 具体参数 | [命令参考](commands.md) | 命令语法，不在其他页面复制 |
| 选择开发流程 | [Workflow 与 Skill 场景](workflows.md) | Manifest 登记的 Workflow 与普通 Skill 用法 |
| 编写/优化 Skill | [Skill 格式与方法](skill-format-guide.md) | Frontmatter、触发、可执行证据 |
| 了解已有资产 | [由 Manifest 生成的目录](agent-skill-catalog.md) | Agent、Skill、Profile、Workflow 列表 |
| 维护仓库与 PR | [贡献指南](CONTRIBUTING.md) | 修改、定向验证、受保护发布 |

## 按需深入

- [SDD 最小路径](runbooks/spec-driven-delivery.md)：跨模块行为或接口变更；单点小修不强制规格文档
- [嵌入式开发约束](embedded-constraints.md)：设备、SoC/MCU、Linux/RTOS 的执行边界
- [运行时与模型边界](architecture/interoperability-boundaries.md)：source、安装、native evidence、认证的区别
- [外部方法与来源](runbooks/practice-source-governance.md)：可信来源、审核与安全
- [维护和发布](runbooks/workspace-maintenance-guide.md)：源码维护、验证和精确 Release
- [故障排查](troubleshooting.md)：已知问题和错误定位

## 历史与研究资料

`docs/changes/`、`docs/migrations/`、`docs/analysis/`、`docs/evals/` 与 `docs/pilots/` 包含历史变更、迁移说明、实验与证据；其中的旧版本、旧命令或未测结论**不能作为当前使用说明**。请使用上方活动入口，并按原始证据身份读取历史材料。

如需审查工具选型的历史观点，参见[参考资料说明](reference/tool-cheatsheet.md)，不要照搬其中已过时的市场比较或安装指令。
