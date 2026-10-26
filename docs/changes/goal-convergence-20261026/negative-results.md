# 负结果与修复边界

1. 初版技能文本增长触发140行及profile footprint限制；保留原限制，压缩重复命令/模板并减少入口总字节，相关门禁复验通过。
2. 独审发现open_items普通下降可清零non_closing_advances，2→1→2构成绕过。修为首次原criterion-closed新证据加净减少才清零；新增回归及独立复现通过。
3. change_kind/adjustment为list时原先TypeError；现先校验字符串并返回ExecutionPolicyError，测试覆盖。
4. 首版Codex能力缺失测试依赖旧provider实际无能力，未来导入后可能失效；改为进程内显式mock拒绝，并断言journal不变，3项fresh通过。
5. strict旧参考到期、当前Harness审核失效、未提交源码和缺签名发布条件均保留，不通过改日期、删门禁、伪造commit或写冻结镜像求绿。
6. devkit export --target codex明确拒绝external-handoff-only目标，符合受管导入边界；未改用直接复制或新fallback。
7. PR #224首轮CI发现reducer跨分支复用previous导致int/set静态类型冲突；三处更名为previous_digests，语义不变。独立复审30项通过，本地mypy 1.14.1及ruff通过；CI所用mypy 2.4.0须由后续CI单独验证。Harness新增真实微修复审查报告并刷新凭据，单项复验通过。
