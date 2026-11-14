# OpenCode 本地任务先导

## 目标与范围

在不调用 Codex/ChatGPT Work 额度或付费模型 API 的条件下，使用官方 OpenCode v2.3.0 与本地 Ollama 执行一个公开开发任务的 baseline/candidate 先导，获取第一份真实原生任务记录。现有 task grader/importer/统计器继续为唯一接续路径；本先导不新建 runtime、scheduler 或生产适配器。

## 冻结的试验范围

- 任务：`tests/fixtures/skill_execution_tasks/targeted-document-edit`，原始任务、初始工作区和现有 case 合同在执行前冻结摘要。case/期望内容不传给执行模型。
- Skill：`adk-adr-writer`，baseline 来源 7aed1d2545babce16c41dc021ead01c8c324ce07，candidate 来源 4f77f795ecfba3e6bb1e167eb27cb84cca796845；只装载各自真实导出的对应 Skill 和它实际引用的资料。
- 宿主：OpenCode v2.3.0，官方 Linux x64 资产 SHA256 fc0f81522aceeabac47693d88389efa2bc517ce74c2c38fd6967819fcc6e4d3b。
- 本地推理：Ollama v0.40.16，官方 amd64 资产 SHA256 87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d；模型仅本地 `qwen3:1.7b`，运行前记录下载得到的完整模型 digest，两个条件使用同一 digest。
- 初始规模：每个条件一次、同一开发任务；baseline 后 candidate。只诊断链路与描述性结果，不据此估计因果时延改善、泛化收益或全体 Skills 成熟度。

## 验收与限制

1. 在隔离的任务目录和配置/数据目录内执行，固定本地 provider，阻止云 provider、subagent、联网工具及任务外写入。不得读取已有账号凭证或改 live 用户资产。
2. 每条件最多300秒，预算到期保留实际中断/失败与产物，不单侧重跑或隐藏失败；安装、模型准备失败记录为环境阻塞。
3. 保留实际命令、退出码、起止时间、宿主版本、模型 digest、完整原始日志/持久会话导出、前后文件摘要。实际加载仅由宿主日志证明。
4. 使用已有 grader 独立验收最终 `work/`；单次产物正确不证明过程权限或不重复副作用。
5. 不确定的 attempts/tool/guardrail/skill 覆盖不能填 true；缺失或不完整 Token/cost 保留 unavailable。先获得原始样本再判断是否可安全转换，不提前捏造适配协议。
6. 该先导不关闭原方案的32次示例试验、独立holdout或收益验收；根据真实记录决定是否值得扩大。
