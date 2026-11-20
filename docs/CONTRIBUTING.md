# 贡献与维护

本文只说明 ADK **源码维护**；普通 Skill 使用者请先读[快速入门](quick-start.md)。构建/管理工具需要 CPython 3.12，部署后的纯 Skill 不要求 ADK Python。

## 开发准备

```bash
git clone https://github.com/jiying2007/agent-dev-kit.git
cd agent-dev-kit
git switch -c fix/your-scope
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[quality]'
```

无仓库写入权限的贡献者先 Fork，并将仓库地址替换成自己的 Fork；不要假设维护仓库允许直接推送 main。依赖、受支持 Python 范围以 `pyproject.toml` 为准。

## 一次改动的最小流程

1. **确认范围**：读取已有 Skill/Contract/Schema/Runbook 与相关负例；已经有权威位置就修改该位置。避免添加同义 Skill、第二个 Manifest 或运行时执行引擎。
2. **实施**：只改必要文件、复用现有代码风格；涉及 API/协议或行为变化时按 [SDD 路径](runbooks/spec-driven-delivery.md) 保留行为 delta 和验收映射。文档改动需核实链接、命令可执行及正文与源码一致。
3. **定向验证**：先跑所改范围的测试；控制面常用入口为：
   ```bash
   bash scripts/devkit.sh validate --strict
   bash tests/run_all.sh --quick
   git diff --check
   git status --short
   ```
4. **提交**：审阅 `git diff`，仅暂存本次范围，提交后通过受保护 PR。代码质量、Shell、类型、契约、全量回归、安全与 Release 结果，以 CI 的**最终提交 SHA**为准。
5. **版本与发布**：每个合入主线的变更必须满足当前受控 SemVer 前移与版本投影一致性；参见[版本与发布命令](commands.md#release)。不可修改旧 tag，不可因为 PR 全绿宣称主线发布完成；合并后核对 fresh-main CI、不可变 Release、消费方精确来源。
6. **结论**：明确哪些验证已经执行，哪些因工具、设备、模型或现场证据缺失而未执行。不得把 `not-measured` 伪装为 PASS。

## 评审重点

- 直接的任务价值与**最小必要 diff**；是否存在旧分支、兼容层、重复路径或文档镜像
- 正常/失败/取消/恢复路径及可复现回归；生产或设备动作不由测试自行授权
- 权限、来源、凭据、文件路径、资源预算与隐私日志
- 模型效果、Token/成本、Runtime 原生触发、产品资格分别列出可核验和不可核验部分

文档只有一份权威解释：用户入口[Usage](usage.md)、CLI [Commands](commands.md)、[Workflow 与任务分层](workflows.md)、维护操作[Runbook](runbooks/workspace-maintenance-guide.md)。历史变更证据保留在 `docs/changes/`，禁止为了缩减目录而破坏可追溯性。

问题报告请附环境、精确 SHA、命令、退出码、最小重现和脱敏日志。敏感信息不要写入 PR、Issue 或公开测试 Fixture。
