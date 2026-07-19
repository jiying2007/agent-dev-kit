# Prompt 对比：external-practice-intake-v1

## Before

- 触发语义偏向“接入子仓”，把 discovery、clone、registry 修改、评分和吸收混在一个入口。
- 默认提示缺少 GitLab/Gitee、OpenAI/Codex、Anthropic/Claude、微信公众号和人工证据的统一边界。
- collector、curator、decision owner、implementer、verifier/publisher 没有明确分权，容易形成自评自批。
- 没有明确要求记录不可迁移缺点、provider degraded、正文/凭证边界、pilot 和退役条件。

## After

`agents/openai.yaml` 的默认提示为：

> Use $adk-external-practice-absorption to review this external practice and produce a governed adoption decision.

新 Skill/Agent/Workflow 将输出约束为：

1. 先归一 `external-practice-candidate/v1`，自动阶段止于 `review-required`。
2. 同时输出可借鉴优点、不可迁移缺点、重复/架构、license/copyright、安全和成本证据。
3. curator 只能给出 `recommend-decision-review|needs-more-evidence`，不得生成批准状态。
4. 独立 owner decision 之后才允许创建 change；实现、验证、pilot、publish、review/retire 继续由不同职责接力。
5. Gitee 空结果固定 `degraded-empty`；官方来源不等于自动采纳；微信公众号只消费 metadata catalog 且正文不落盘。

## 路由与安装验收

- Positive：`吸收 Gitee GitHub GitLab 的 Agent 工程实践` 命中 `external_practice_absorption`。
- Negative：`直接实现已经批准的普通功能` 不命中本 Skill。
- `research-intake` profile 单独执行 workflow closure 必须失败；显式添加 `--with-optional-skill adk-external-practice-absorption` 后才通过。
- Skill 位于 `optional-skills/`，不会随默认 profile 隐式安装。
