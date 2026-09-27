# 设计

1. 在现有 `adk-interface-contract-design` 增加条件性工具副作用步骤，不新增 Skill。只读工具只需确认效果分类；写入/不可逆工具必须冻结授权主体与时点、目标与参数、失败/未知结果、op-id 与重放处理。
2. 将细节放在 `references/tool-effect-contract.md`，保持 Skill 入口简短。审批和实际生效分开记录；handoff 后工具调用重新检查；暂停状态仅从可信存储恢复。
3. 用 TSV 补齐 `governance-eval-guardrail-regression-dataset` 已声明的路径，覆盖 positive、negative、adversarial、borderline。现有 `test_skill_governance.py` 检查所有 suite 数据集存在及四类样本平衡，防止未来出现静默悬空引用。
4. Skill 入口增长 461 UTF-8 字节；新增按需读取参考文档使含该 Skill 的 profile 潜在完整源码增长 2519 字节。按 `profile-footprint` 当前工作树实测更新七个受影响 profile 的源码增长棘轮；`incident-response` 未包含该 Skill，基线不变。这是源文件大小审查，不代表初始运行上下文或模型 token 测量。
5. 通过官方 `agent_dev_kit.versioning sync-identity` 同步 7.12.2 到 manifest、package、README、CONTEXT、M5 campaign 与 `.version-lock`，满足 PR 的版本前移契约。

回滚：撤销这组 Skill、参考文档、fixture 与测试改动即可恢复原契约；不涉及数据迁移或运行态回滚。
