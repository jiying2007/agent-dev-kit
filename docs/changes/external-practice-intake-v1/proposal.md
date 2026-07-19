# 变更提案：external-practice-intake-v1

## 背景

- `llm_agent` 已分别具备 GitHub OSS discovery、手工 Gitee URL 账本、微信公众号 metadata-only 归档和 ADK 官方文档 freshness gate，但四条链路使用不同入口、schema、状态和报告，无法统一去重、复审、退役或解释“为什么形成 Agent/Skill/Workflow”。
- GitLab 没有对等 metadata provider；Gitee 只有 URL 识别，没有 API discovery、降级状态或 rate-limit/空结果证据。
- 旧 `adk-intake-workflow` 仍描述直接 `git clone`、手工修改 registry 和同步子仓，违反当前 commit-snapshot、review-required、source-to-live 与外部写入边界。
- 用户明确要求增加 Gitee 范围，按统一多源建议落地，并采用终态硬切换：不保留旧 CLI/schema 兼容层，清理活跃引用和重复资产。

## 问题陈述（单问题）

- 本变更只解决一个明确问题：外部优秀实践没有统一、受限、可复现且能一直追踪到 ADK change artifact 的 intake 控制面。
- 触发证据：`scripts/discover-oss-repos.sh` 只实现 GitHub REST；`manifests/oss_discovery_sources.json`、`manifests/oss_continuous_operation.json` 和微信公众号账本各自为政；GitLab 搜索只出现在 PR contract；旧 Skill 的命令与当前安全治理冲突。

## 目标

1. 建立单一 `scripts/practice-intake.sh`，统一 GitHub、GitLab、Gitee、OpenAI/Codex 官方、Anthropic/Claude 官方、微信公众号和人工 URL/本地证据输入。
2. 所有 provider 输出同一个 `external-practice-candidate.v1` JSONL 合同，并由统一 policy 校验来源、权限、freshness、license/版权、hash、边界、去重和 review 状态。
3. 网络 provider 只能在显式 `--allow-network` 下执行；默认 fixture/local-input/report-only，不 clone、不安装、不执行外部代码、不修改 registry/ADK/live runtime。
4. 生成统一 review queue、cycle evidence 和候选形态建议；所有候选固定 `review-required`，不得自动形成 ADOPT 或运行资产。
5. 只有独立 owner decision 和 ADK change artifact 才能进入 Agent、Skill、Workflow、Script、Manifest、Runbook 的实现与验证。
6. 用新的 `adk-external-practice-absorption` Skill、外部实践 curator Agent 和 absorption Workflow 替换旧 `adk-intake-workflow`，明确发现、评估、实现、pilot、发布和退役边界。
7. 删除旧 discovery/score/queue/continuous/WeChat ledger 公共入口、manifest、fixture、测试和活跃文档引用；不提供 wrapper、alias 或旧 schema reader。

## 非目标

- 不穷举互联网内容，不把采集量、star 或资产数量作为质量 KPI。
- 不在新工具中抓取微信公众号正文、绕过登录/CAPTCHA/anti-spider、保存版权正文或使用代理池/身份轮换。
- 不把官方来源自动等同为平台中立 ADK 规则；Codex/Claude 专属事实必须留在 target/reference 边界。
- 不自动 clone、注册子仓、吸收 ADK、创建 commit、push、tag、publish、启用 MCP/Hook/runtime 或写 `~/codex`、`~/.codex`。
- 不重写历史 `reports/oss-*`、历史微信报告或 adoption matrix provenance；它们不是活跃入口。
- 不在本 change 内执行真实长期自动化、付费 API、外部账号申请或 owner active promotion。

## 上下文充分性检查

- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（网络、凭证、prompt injection、license、并发、性能、兼容）
- [x] 已明确验证命令与通过标准
- [x] 外部不可控条件有降级合同：Gitee 空结果/服务异常不得伪装成“无候选”；无 token 只能读取公开元数据

## Core/Optional 边界检查

- [ ] 属于通用核心能力（core）
- [x] 属于场景化能力（optional）
- 归属结论与理由：根仓 intake 工具属于 `llm_agent` 治理面；ADK Skill/Agent/Workflow 只在外部实践研究与吸收场景触发，不应进入每个开发任务的默认上下文。新 Skill 进入 optional catalog，Workflow/Agent 只由该场景组合调用。

## 变更重复性检查

- 已检索：旧 `adk-intake-workflow`、OSS P1-P4、WeChat intake、`official_docs_freshness_gates.json`、`external_agent_pattern_contracts.json`、Knowledge Hub harness decision。
- 本次差异：不复制既有 repository lifecycle、官方 freshness 或微信采集器；新增的是跨来源统一 candidate/queue/cycle 合同和 provider adapter，并把旧发现层硬切掉。批准后的 repository onboarding/removal 继续是独立生命周期，不是 intake 兼容层。

## Breaking Change 检查

- [ ] 否：不涉及兼容性破坏
- [x] 是：涉及兼容性破坏

硬删除并不再识别：

- `scripts/oss-intake.sh`
- `scripts/discover-oss-repos.sh`
- `scripts/run-oss-intake-cycle.sh`
- `scripts/check-oss-intake-ledger.sh`
- `scripts/score-oss-candidates.sh`
- `scripts/generate-oss-intake-approval-queue.sh`
- `scripts/check-oss-approval-queue.sh`
- `scripts/generate-wechat-intake-ledger.sh`
- `scripts/check-wechat-intake-ledger.sh`
- `scripts/check-oss-intake-fixtures.sh`
- `scripts/onboard-oss-candidate.sh`
- `manifests/oss_discovery_sources.json`、`oss_candidate_scoring_policy.json`、`oss_continuous_operation.json`、`oss_intake_approval_queue.json`
- 旧 OSS candidate JSONL 作为新命令输入
- `adk-intake-workflow`

迁移目标只有 `scripts/practice-intake.sh`、`scripts/onboard-reference-repository.sh`、`external-practice-candidate.v1` 和新的 ADK absorption assets。没有弃用期、兼容 wrapper、双写或旧字段回退。回滚只能整体撤销本 change，不允许恢复双入口。

## Spec 链路检查

- requirements 基线：本 proposal 的七项目标、非目标、硬删除清单与验收边界。
- design 决策：`design.md` 的 provider adapter、统一 schema、独立 decision、report-only cycle、硬切迁移和安全预算。
- tasks 追溯：`tasks.md` T1–T7 覆盖合同、实现、ADK 资产、硬切、验证、复审和归档。
- 跨仓架构：`llm_agent/architecture/external-practice-intake-terminal.md`。

## 安装范围与依赖边界

- 根工具：project-bound，只在 `llm_agent` 运行，Python 3.11+ 标准库，不读取目标仓代码、不执行第三方内容。
- ADK Skill：optional/global-ready；Agent/Workflow 由显式 intake/absorption 意图调用。
- 官方与微信：只消费受治理本地 manifest/catalog；实际网页研究仍由各自受限 transport 完成。
- Forge provider：HTTPS GET、allowlisted host、只读 token env、响应/时间/候选数量上限、日志不输出 token。

## Prompt 回归证据计划

- before：相同 GitHub/Gitee URL、GitHub fixture、官方 manifest 和 WeChat catalog 需要三套入口，GitLab 无法生成候选。
- after：六类来源经单一 CLI 输出同 schema、唯一 candidate ID、统一风险和 review queue。
- 失败样例：非法 host、非 HTTPS、控制字符、超量响应、token 字段泄漏、空 Gitee 搜索、未知 provider、旧 schema、正文持久化、自动 ADOPT/写入请求全部保留负 fixture。

## 收敛模式与退出条件

- 当前模式：planning；change governance 通过并切换 `applied` 后进入 execution。
- 完成声明：活跃入口只有 `practice-intake`，六类 provider 具有正负证据，旧入口/manifest/Skill 无活跃引用，ADK/root 定向与全量门禁通过，独立 review 无 blocker/major。
- 真实网络 source 只需至少 GitHub/GitLab/Gitee 各完成 fixture contract；若受网络/服务限制，live smoke 必须记录 `not-run` 或 `degraded`，不能用 fixture 冒充生产证据。

## 备选方案与取舍

- 方案 A：给每个来源增加独立 Agent/Skill/脚本。拒绝：扩大资产数量、状态割裂、重复安全逻辑和路由冲突。
- 方案 B：在旧 OSS JSONL 上继续加 GitLab/Gitee/文章字段。拒绝：repository 专属 score/字段无法表达官方文档与微信，且维持双重语义。
- 方案 C：统一 candidate/decision/cycle 控制面，provider 只做纯适配，批准后再分流到 repository lifecycle 或 ADK change。采用。

## 风险与回退

- 供应链与 prompt injection：外部字符串始终视为数据；不渲染为命令、不执行、不保存正文；控制字符和长度超限 fail closed。
- API 漂移：provider 解析必需 identity/url，其他字段允许显式 unknown；响应不合同时失败并保存脱敏 transport evidence。
- Gitee 当前搜索空结果争议：空列表标记 `degraded-empty` 并进入 review queue，不声明 source clean。
- 误删调用方：删除前全库调用检索；增加 active-tree legacy-reference gate，排除历史 reports/archive provenance。
- 回退：整体 revert 本 change；没有数据库、运行目录或远端状态迁移。禁止以兼容 wrapper 作为回退。
