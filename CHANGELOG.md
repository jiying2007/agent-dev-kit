# Changelog

## Unreleased

## v3.1.0-rc.7 (2026-08-02)

### 新增
- 增加 task-cost profile 与 CLI receipt，用有界字段表达任务复杂度、上下文预算、验证强度和归档候选要求。
- Knowledge Hub 上下文查询增加显式项目路由、分层 receipt、review SLA packet 与有界 capture summary。

### 改进
- Token 预算门禁区分 soft/hard limit，并为 AGENTS、Skill、Workflow 与 manifest 提供可解释余量。
- 根工作区门禁区分 `working-tree` 与 `release-clean`，开发态绑定同轮 fingerprint，发布态继续要求 ADK clean state。
- Codex 资产交付增加 plan v3 precondition、按需 workflow activation、成本投影和 already-applied no-op 收敛。

### 发布边界
- RC7 使用 checksum-bound RC6 artifact 执行本地升级、候选回滚和 RC6 hash 恢复演练。
- 本轮授权 source commit 与 push；不创建 tag、远端 Release，不提升 Knowledge Hub active 状态。

## v3.1.0-rc.6 (2026-07-31)

### 新增
- MCP `2026-07-28` protocol governance contract 经固定 Go SDK 的 schema、client/server、auth 和 rollback 证据后激活；runtime 与 Tasks、Apps、extensions 继续关闭。
- 嵌入式远程调试增加分层连通性、设备失联熔断、artifact/mutation gate 和 HIL 分阶段扩大合同。
- 目标架构报告支持由机器 SSOT 管理连续 G11+ 项目级优化条目。

### 发布边界
- RC6 通过 RC5 到 RC6 本地 artifact 升级/回滚演练建立新 release baseline。
- Codex source-to-live 未自动执行，保持独立 owner 授权门禁。

## v3.1.0-rc.5 (2026-07-19)

### 新增
- 增加平台中立 `skill_invocation` SSOT 和 direct-target mapping；Claude Code 支持 `explicit-only`，未核验等价字段的 target fail closed，Codex 继续由 external handoff adapter 承接。
- 增加 task-package v2 typed validator，区分 decision/research/prototype/implementation，并用 permission/exit gate 阻止探索票直接进入实现。
- 增加 architecture hotspot/YAGNI scope 与 prototype evidence provenance/retention 合同。

### 破坏性变化
- 删除 task-package v1 活跃合同与 reader，不补默认字段、不双写；所有机器消费任务包必须迁移到 v2。
- Codex Skill metadata 硬切官方嵌套 `interface` 结构；顶层 legacy metadata 与显式 `allow_implicit_invocation: true` 不再接受。

### 门禁
- 新增 invocation target mapping、未知 override、work-item 越权、prototype 缺 provenance、架构无理由扩域的正负回归。
- external source 只吸收方法，不安装、复制或运行 `mattpocock/skills`、Claude plugin、hook/MCP 或 in-progress Skill。

## v3.1.0-rc.4 (2026-07-19)

### 新增
- 增加 `external-practice-curator`、显式 opt-in 的 `adk-external-practice-absorption` 和 `external-practice-absorption` Workflow，统一承接 GitHub、GitLab、Gitee、OpenAI/Codex 官方、Anthropic/Claude 官方、微信公众号与人工证据的候选审查和独立决策 handoff。
- 增加 `research-intake` profile 的 Agent 默认 Skill 闭包，并保留 optional Skill 必须显式选择的安装边界。

### 破坏性变化
- 删除 `adk-intake-workflow`，不提供别名、warning wrapper 或双写兼容；调用方必须迁移到新的 candidate/decision/change 工作流。
- 外部实践 collector/curator 固定为 `read-only`、`report-only`，不得自批、自动复制、安装、提交、发布或写 live runtime。

### 修复
- file-mode 与 security inventory 在 live Git 工作树中跳过已删除路径的内容扫描，删除本身继续由 status、inventory 和 review 门禁负责；显式只读 inventory 仍对缺失文件 fail closed。
- Workflow 合同与 taxonomy 测试同步一等 Workflow 数量、optional closure 和 lifecycle 顺序。

## v3.1.0-rc.3 (2026-07-18)

### 修复
- 根工作区性能包装器现在执行 quick timing 的严格预算门禁；ADK quick suite 执行 quick manifest validation，把产品成熟度与 catalog/taxonomy 重型回归保留在 full（根性能包装器仍单独执行产品成熟度），避免重复工作并为 120 秒预算保留抖动余量。
- install manifest、Draft 2020-12 schema、copy-only installer 和用户文档统一；关键 routing、dependency、reference、context、change-set 与空 MCP 合同改为 typed fail-closed schema。
- Harness readiness 要求结构化权限边界，拒绝否定语境伪证据，并对未来或超过 freshness 窗口的验证日期输出 blocker。
- Python 打包元数据迁移到 PEP 639 SPDX license 表达式，并增加 Python 3.11/3.12 Docker 本地 CI parity runner：源码快照只读、固定非 root 身份、gates 无网络、dependency audit 独立联网，并核验 base/definition/image identity；本地结果不能替代 release provenance 或远端 CI 状态。

### 破坏性变化
- 发布支持基线提升到 Python 3.11+，运行依赖固定为 `PyYAML==6.0.3` 与 `jsonschema==4.26.0`；CI 最低版本同步到 3.11。
- 关键 nested manifest object 现在执行 typed schema 并拒绝未知字段；自定义 manifest 升级前需运行 `bash scripts/devkit.sh validate --strict`，修正错误类型，并把确需保留的产品级扩展迁移到顶层 `x-<name>` namespace。

## v3.1.0-rc.2 (2026-07-13)

### 修复
- direct target 输出改由 versioned `TargetContract` 与单一 `TargetAdapter` 生成；Claude Code/OpenCode 使用原生 `agents/<name>.md` 与 `skills/<name>/SKILL.md`，Hermes 明确为 Skill-only。
- Agent/Skill frontmatter 补齐目标必需字段、显式 Agent permission profile 和 `metadata.adk` provenance；Skill support directories 随主文件确定性导出。
- export/install 共用 renderer；export manifest 升级到 v2，install plan 升级到 v2，receipt 升级到 v3，并保留 v1/v2 receipt rollback 读取。
- install plan 绑定 active receipt SHA256、UUID、时区时间与 24 小时 TTL 上限；legacy fallback 演练会从保留的 rc.1 artifact 重装并比对 managed hashes。

### 门禁
- direct target 保持 `experimental`，只有真实 runtime discovery/load/trigger/permission smoke 完成后才允许提升 stable。
- manifest schema 升级到 3.1.0，并由 `jsonschema==4.23.0` 按 Draft 2020-12 实际执行。
- CI 增加 ShellCheck、Ruff、pip-audit 和 OpenSSF Scorecard；release build 校验 SPDX SBOM，并由 SHA-pinned `actions/attest` 生成 provenance。
- 性能基准增加 CLI cold-start、10x plan/I/O 与 peak allocation；effect eval 增加 24 个 OOD/adversarial route+safety+trace+outcome case，并要求 routing ablation 至少产生 0.1 的准确率差值。
- `3.1.0-rc.2` 修复 target conformance，不代表 M4/M5 或 terminal maturity 认证。

### 增强
- 新增 `adk-runtime-router` 核心技能，作为 adk-first 运行时路由入口，统一 primary/supporting/fallback 裁决。
- 新增 `adk-test-strategy`、`adk-code-review-loop`、`adk-parallel-agent-governance`、`adk-worktree-governance`、`adk-branch-closeout` 五个核心技能，减少对 Superpowers TDD/review/parallel/worktree/branch closeout fallback 的默认依赖。
- 扩充 `adk-requirements-triage` 与 `adk-systematic-debugging` 自然语言触发覆盖，降低真实任务漏匹配概率。
- 新增 `docs/reference/fallback-sunset-matrix.md` 与 `fallback-sunset-matrix.tsv`，跟踪 fallback 到 adk 原生能力的下线状态。
- 新增 `scripts/check-fallback-sunset.sh`、pilot 证据库和嵌入式优先模板，防止在缺少真实能力面证据时提前宣布 sunset。
- 调整 `adk-test-strategy` 为嵌入式优先、兼容通用工具链脚本的测试策略定位。
- 强化 fallback 下线门禁：逐行执行 `devkit.sh match --text`、校验命中 skill 属于等价能力、检查 active-fallback 复核日期，并输出 routing/profile/pilot/handoff/live replacement score。
- fallback 下线门禁新增 `--score-tsv` 与 `--summary-json`，并检查 pilot index 与 evidence 文件状态、章节是否一致。
- fallback 下线门禁新增 `live_requirement`、按状态评分阈值和 `scripts/pilot-readiness.sh` 独立 pilot 成熟度检查。
- 将 adk 定位修正为嵌入式全栈，覆盖 SoC、MCU、Linux、RTOS、驱动、组件、设备应用、上位机、产测诊断工具和交付验证，不扩展到通用 Web/互联网后端/云原生。
- 扩展嵌入式全栈范围为完整工程闭环：芯片/板级约束、启动链、BSP/rootfs、OS/runtime、验证、发布、量产和现场维护；新增 `adk-production-field-readiness` 承接量产/现场 readiness。
- 为 active-fallback 能力补充 discovery、子代理审查、skill 生命周期、长任务恢复和嵌入式全栈测试矩阵模板。

### 修复
- 生命周期文档移除未落地的 `adk-*workflow` 与 `adk lifecycle` 占位入口，改为当前 `scripts/devkit.sh` 真实命令。
- 维护文档统一使用 `adk-*` 技能名称，减少 Superpowers 迁移期命名漂移。

## v3.1.0-rc.1 (2026-07-13)

### 新增
- 新增 `doctor`、`lock`、`eval campaign/certify` 和 `release rehearse` 公共入口。
- 新增 60 任务、Codex/Claude、baseline/ADK、3 trials 的软件 M5 评测契约，固定模型、预算、重复试验和统计门槛。
- 新增 export/install/rollback/campaign 的 portable single-writer lock，支持显式状态检查和基于 lock ID 的人工清理。
- 新增 checksum 约束的本地 release 升级/回滚演练，校验 top/source manifest、receipt 和受管资产 hash。

### 改进
- 将确定性 matcher 收敛为一次结构化加载的 Python core，保留 `skill-match.sh` 参数、输出和退出码兼容。
- campaign 结果逐任务原子落盘，支持 resume，并绑定 manifest、contract、tasks、frozen plan、runtime 版本、模型和 record hash。
- Claude 主调用与一次重试的最坏费用受 `$150` 总上限约束；重试的 latency、token 和 cost 全部进入非回退门禁。
- 安装 receipt 升级为 `v2`，校验 receipt、替换备份和前序 receipt 的 SHA256，同时保留 `v1` 升级回滚兼容。
- runtime 调用增加有界超时和异常归一化；writer lock 禁止清理仍存活 owner，export 双重故障保留人工恢复目录。

### 成熟度边界
- `3.1.0-rc.1` 是 M5-ready release candidate，不代表已认证 M5 或 terminal maturity。
- 最终 `3.1.0` 仍要求 30 天试点、至少一个独立真实软件仓、第二位 operator、双 runtime campaign 和完整 field evidence。

## v2.9.0 (2026-05-17)

### 破坏性变更
- 移除重复调试技能 `adk-diagnose-loop`，统一由 `adk-systematic-debugging` 承接诊断闭环。
- 移除重复产物门禁 optional skill `adk-artifact-gated-lite`，统一由核心 `adk-artifact-gating` 承接高风险门禁。
- Codex 交付硬切换为 `agent-dev-kit -> ~/codex -> ~/.codex`，禁止直接安装到 `~/.codex`。

### 增强
- manifest 新增一等 `workflows` 与显式空 `mcp_servers` 声明。
- Codex handoff 新增 `workflows.json` 与 `mcp_servers.json` manifest fragment。
- 严格校验新增 context layer 路径、workflow 声明和 SKILL.md 入口长度门禁。
- 长 SKILL.md 拆分到 `references/details.md`，减少默认上下文加载。

## v2.8.0 (2026-05-12)

### 修复
- manifest.yaml: 修复 33 个 skill 的重复 quality_tier YAML 键
- manifest.yaml: 补充 7 个缺失 Profile 定义 (personal-core, embedded-fullstack, team-core, openspec-driven, large-refactor, incident-response, research-intake)
- 文档引用: 修复 7 个文件中的版本锁定引用 (统一为 2.8.0)
- 导航链接: 修复 NAVIGATION.md 3 个断裂 Runbook 链接
- Runbook 索引: 修复 runbooks/README.md 3 个错误文件名
- 脚本引用: 修复 check-global-codex-health.sh 和 check-adk-harden-readiness.sh 路径引用
- 统计数据: 更新 README.md 和 AGENTS.md 中的过时统计数字

### 统计
- Agents: 10 个
- Core Skills: 33 个
- Optional Skills: 9 个
- Profiles: 10 个 (新增 8 个)
- Scripts: 26 个

## v2.7.0 (2026-05-10)

### 增强
- VibeFlow 生命周期框架吸收 (8 阶段: Spark→Design→Tasks→Build→Review→Test→Ship→Reflect)
- Gate 机制设计原则 (4 问评估标准)
- 知识分层架构 (L0-L4) 文档化
- 仓库深度分析报告更新

### 新增
- docs/workflows/lifecycle.md: 生命周期工作流文档
- docs/workflows/gate-design.md: Gate 设计原则文档


## v2.6.0 (2026-05-06)
### 新增
- 脚本 smoke 测试：test_scripts_smoke.sh 覆盖 11 个脚本

## v2.5.0 (2026-05-06)
### 修复
- Trigger 冲突：修复 6 个 skill 的 trigger 重复
- Skills last_updated 日期更新为 2026-05-06

## v2.4.0 (2026-05-06)
### 修复
- manifest.yaml optional_skills 列表错误修正
- Docs 中 7 个脚本引用路径修正
- adk-data-fetch SKILL.md 创建

## v2.3.0 (2026-05-06)
### 增强
- 10 个 Agents 全部充实（50-67L → 103-123L）
- 7 个 Optional Skills 全部充实（59-77L → 128-152L）

## v2.2.0 (2026-05-06)
### 增强
- 28 个 Core Skills 全部充实（65-106L → 80-195L）
- Skill 内容质量测试：test_skill_content.sh（196 检查点）

## v2.1.0 (2026-05-06)
### 增强
- Routing 全覆盖：28/28 skills
- user-story-template 扩充（29L → 235L）

## v2.0.0 (2026-05-05)

### 新增
- Anti-Rationalization 机制：每个 p0 skill 添加"合理化借口拦截"表
- Skill 路由表：manifest.yaml 新增 routing 字段，支持中英文意图映射
- 阻塞模板：templates/blocked.md 和 ready.md
- 执行计划模板：templates/exec-plan.md（六要素）
- 质量评分卡：templates/quality-score.md（五维度）
- Agent 交接协议：templates/agent-handoff.md
- 健壮性规范：SKILL.md 新增 robustness 章节要求
- 渐进式披露：skill references/ 子目录支持
- Profile 冲突检测：manifest.yaml conflicts_with 字段
- Skill 依赖图：manifest.yaml depends_on/enables 字段
- 新增 Skill: adk-structured-requirements-questioning, adk-code-simplification, adk-context-engineering
- 新增 Skill: adk-chinese-commit-conventions, adk-chinese-code-review
- 新增 Optional Skill: adk-fetch-url-content, adk-email-imap-fetch
- 文档导航: docs/NAVIGATION.md
- 测试: test_anti_rationalization.sh, test_routing.sh, test_skill_dependencies.sh, test_profile_conflicts.sh

### 统计
- Agents: 10 个（不变）
- Core Skills: 28 个（+6）
- Optional Skills: 9 个（+2）
- Profiles: 10 个（不变，新增 trigger_examples）
- Templates: 5 个（新增）
- Routing: 21 条意图映射（新增）
- Tests: 25 个测试文件（+4）

### 修复
- 版本撕裂：manifest(1.0.0) vs README(0.3.0) 统一为 2.0.0
- 配置冲突：manifest default_mode 从 symlink 改为 copy

### 改进
- 42 个文档新增统一导航索引
- Profile 支持中文触发词路由（intent_zh + trigger_examples）
- 生产运维脚本验证和测试覆盖

## v1.0.0 (2026-05-02)

- 初始生产级发布
- 10 Agent + 22 Skill + 7 Optional Skill + 10 Profile
- Evidence Index 机制
- propose→apply→verify→review→archive 工作流状态机
- 24 脚本 + 21 测试文件 + 42 文档 + 26 Runbook

---

# 变更日志 - 1.0.0

## 版本信息
- 版本号: 1.0.0
- 发布日期: 2026-05-05
- 维护者: aiot03

## 变更内容

### 新增功能
- 完善使用指南和示例文档
- 增加最佳实践和故障排除指南
- 增加贡献指南
- 完善安装备份、回滚机制
- 增加健康检查和监控能力
- 增加版本锁定和升级路径

### 改进优化
- 增强测试覆盖
- 完善质量门禁
- 优化文档体系

### 已知问题
- 无

## 升级指南
1. 备份当前版本
2. 下载新版本
3. 运行健康检查
4. 验证功能

## 相关链接
- 文档: docs/
- 快速入门: docs/quick-start.md
- 故障排除: docs/troubleshooting.md
