# ADK 快速入门

## 已经部署 Skills：直接使用

向目标 Agent 说明**要做的事、已有资料、限制和完成标准**即可。无需记忆 Skill 名称、额外启动 ADK Python 或为单点修复创建完整 SDD/Goal/Workflow。

例如：`定位这条 UART 超时的根因，先复现和做定向回归，不修改其他模块`。实际是否发现、加载、触发 Skill，由目标 Runtime 的原生证据决定；**源码中存在 Skill 不等于目标运行时已安装**。

使用方法见[按任务使用](usage.md)，可用资产以根目录 `manifest.json` 和[资产目录](agent-skill-catalog.md)为准。

## 维护 ADK 源码：Python 3.12

ADK 的**构建、管理、验证、发布控制面**只支持 CPython 3.12.x；纯 Skill 资产部署后不依赖 ADK Python。开发机另需 Git、Bash 和验证脚本所需的工具。

```bash
git clone https://github.com/jiying2007/agent-dev-kit.git
cd agent-dev-kit
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[quality]'
bash scripts/devkit.sh doctor --summary-json
bash scripts/devkit.sh validate --strict
bash tests/run_all.sh --quick
```

上述检查只证明相应源码/环境检查结果，不证明某个外部 Runtime 已通过 native discovery/load/trigger，也不代表真实模型效果或产品现场资格。

## 需要安装或导出到目标环境

先查[安装与导出](usage.md#3-安装和导出)及[命令参考](commands.md#install)。必须先生成并检查 plan，确认受管路径、冲突与可回滚证据，再经目标运行时自己的安装/接入流程执行；不默认写入用户 `HOME` 或自动触发发布。

Codex 使用外部 source-to-live 交接链；不要把 ADK 源码仓当成直接写入 `~/.codex` 的安装器。Claude Code/OpenCode 的 direct target 与实际运行时验证要分别判断。

## 下一步

- [Workflow 与普通 Skill 的区别](workflows.md)
- [SDD：规格驱动交付](runbooks/spec-driven-delivery.md)
- [维护者贡献指南](CONTRIBUTING.md)
- [故障排查](troubleshooting.md)

版本、Release、Runtime 与 Product 资格是独立事实，不从一次成功检查自动继承。
