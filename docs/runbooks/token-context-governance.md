# Token Context Governance Runbook

## 目标

保真省 Token 的目标不是少看信息，而是少读噪音、保留证据、必要时回退原文。任何压缩摘要都必须能回答三个问题：原文在哪里、置信度多少、什么情况下继续读原文。

## 读取层级

| Tier | 默认场景 | 证据要求 |
|---|---|---|
| L0 | 新项目认知、入口定位 | `PROJECT_MAP.md`、目录摘要、测试入口 |
| L1 | 低风险 bug、局部改动、常规日志 | 摘要 + `raw_evidence` + `confidence` |
| L2 | 测试失败、接口变化、根因未明 | 局部原文窗口、调用方、关键 diff、错误栈 |
| L3 | 高风险任务或交付争议 | 完整原文、完整日志、完整 diff |

## 上下文预算模式

使用 `templates/context/context-budget-profile.md` 为每个中大型任务记录 `task_type`、`risk_level`、`budget_profile`、`read_tier`、`compress_allowed`、`raw_required`、`raw_evidence` 和 `fallback_condition`。

| 模式 | 适用场景 | 默认策略 |
|---|---|---|
| 极速 | 扫仓、入口定位、候选文件发现 | L0/L1，激进压缩，必须保留原文入口 |
| 均衡 | 日常编码、低中风险 bug | L1/L2，摘要先行，关键窗口回读 |
| 精确 | 根因未明、接口变化、代码 review | L2，少压缩，多读调用方、测试和配置 |
| 审计 | 安全、权限、支付、迁移、生产事故 | L3，不压缩结论证据，只做去重、排序或脱敏 |

简化规则：粗看开压缩，精看限压缩，审计看原文。出现 `HOT`、`CTX_PRESSURE`、阶段切换或目标切换时，先产出交接摘要，再用预算配置限制下一阶段只读取必要证据。

## 可压缩对象

- 只读命令：`git diff`、`git status`、`git log`、`rg`、目录清单。
- 测试与服务日志：优先 `pytest -q`、`npm test -- --runInBand`、`docker logs --tail 100`。
- 大 JSON 或结构化输出：先抽关键字段，再保留原始文件路径。

## 不得压缩代替审查

- 写操作、删除、移动、部署、数据库写入和生产变更命令。
- 安全审计、权限系统、支付逻辑、数据库迁移、生产事故、协议兼容、加密签名和性能瓶颈分析。
- 摘要缺少错误栈、迁移日志、调用方、权限条件、金额单位或签名字段时，必须回退 L2/L3。

## 证据保留

使用 `templates/context/tool-output-summary.md` 记录摘要，使用 `templates/context/raw-evidence-index.md` 登记完整材料。敏感日志先脱敏，密钥、账号和隐私内容不得写入长期归档。

## 预算分配建议

| 任务类型 | project_map | search | source | logs | diff | docs |
|---|---:|---:|---:|---:|---:|---:|
| exploration | 30 | 30 | 20 | 10 | 0 | 10 |
| bugfix | 10 | 15 | 40 | 25 | 5 | 5 |
| review | 5 | 10 | 20 | 10 | 45 | 10 |
| audit | 5 | 5 | 35 | 20 | 25 | 10 |
| handoff | 20 | 10 | 20 | 10 | 20 | 20 |

比例用于指导上下文打包，不是硬性配额；高风险项始终优先满足原文证据。

## 项目索引

长期项目维护 `templates/context/project-map.md` 的落地副本。只记录入口、测试、禁读目录、高风险区域、常见坑和 `Last Verified`，避免把一次性日志写成长期事实。

## 验证

```bash
scripts/check-token-budget.sh
scripts/validate-assets.sh --strict
tests/test_token_budget.sh
```
