# Workflow / Skill 质量、性能与兼容源治理 — 需求

- 用户授权全面优化现有 Workflows、Skills、Agent 路由、冗余与成本，但不能以假证据或降门禁宣布产品终态。
- 修复已观察到的 skill-curation 的 package 阶段漏声明；当前校验器只包含式检查而遗漏正文多余阶段。
- 区分写驱动源码和 Bring-up/真实设备联调的意图；禁止宽泛的“自动推进”“文档审查”误触发量产或需求询问。
- 发现版本/来源未前移的 PR 时在下载完整 CI 依赖与跑三版本全量回归前尽早失败。
- 官方 Python 3.8 支持本轮保留，已有必需 deterministic-eval-package 汇总 job 使用 always() 明确拒绝 3.8/3.11/3.12 的失败；暂不改变服务器 Ruleset。
- 残留的 v1 schema 与 Python 3.8 helper 仅当没有真实消费者且有迁移证据才能退役。本轮无真实 Runtime Token/用户满意度数据，不伪造收益或生产资格。

## 不包含

- 不新增 Skill、Agent、Runtime、Goal 引擎、外部服务、Credentials、模型回合或现场操作。
- 不发放人类审查权、设备写权限、release/production 资格或删除历史事件/制品。
