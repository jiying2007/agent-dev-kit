# 设计与来源取舍

[Pydantic Evals](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_evals/README.md)展示类型化 case/dataset/evaluator 分层；其 [许可](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_evals/LICENSE)为 MIT，而宿主项目当前 [要求 Python ≥3.10](https://github.com/pydantic/pydantic-ai/blob/main/pyproject.toml)。[Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai)具有可复用的评测/日志/测试实践，但同样 [要求 Python ≥3.10](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/pyproject.toml)，并在 [安全政策](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/SECURITY.md)中明确评测任务、日志和数据集可能带来代码执行或敏感数据风险。均不作为 ADK 3.8 运行时依赖。

ADK 当前 `eval_catalog` 只审计静态声明，不执行 grader；因此只收紧现有字段合同：grader 与 fixture 使用封闭字段，JSON 解析拒绝重复键。它没有引入可执行 evaluator、脚本路径或外部模型客户端。既有 `grader_executed=false`、`runtime_eval_executed=false`、`release_authorized=false` 保持不变。

新候选完整对照见 `candidate-repositories.md`。其 HEAD exact commit 未经本轮可信来源锁核验，保持 `review-required`；后续若要导入单项资产，先核 commit、许可、依赖与运行权限并走独立 owner 决策。
