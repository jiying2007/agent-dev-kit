# 最小来源刷新设计

设计者与实际来源复核者为 ai/root/architecture_audit；实施者为 ai/root。精确设计见 evidence/proposed-changes.json，原始检索观察见 evidence/primary-source-observations.json；这些材料在生产 manifest 修改前生成。

仅修改 manifests/external_agent_pattern_contracts.json 的两条 source_ref 及 last_updated，并同步 manifests/skill_reproducibility_contracts.json 的 AST04/AST05 crosswalk 和 last_updated。2026-11-22 是本地保守的 30 天复核期限，不表示上游保证有效。没有修改 expiry gate、schema、运行权限、安装范围或其他来源日期。

OWASP 来源固定到 d6f7d7d0de314f52a83a85d1828e06ab096e595c；AST05 改为 Untrusted External Instructions，原有 safe parser、bounded schema 和 no executable deserialization 控制保留在 AST04。保持 evolving/observe-only，不导入 Universal Skill Format、不复制第三方正文或声明 OWASP 认证。没有审读所链接白皮书全文。

论文读取固定 v2 的方法、维护结论与有效性限制，只增强既有可维护性方法。arXiv 非独占发布许可不等于论文、数据集或复现代码的复用许可；不导入这些材料、不推断本地效果。

两个 manifest 均不属于当前 Harness 61 个绑定 source refs。验证仍实际调用已有 receipt validator 与当前 gate；若摘要相符，不重签或移动 Harness 的真实审核时间。回滚为本提交的 metadata/crosswalk 反向变更，会重新暴露真实过期状态；不得把回退当作来源已有效。
