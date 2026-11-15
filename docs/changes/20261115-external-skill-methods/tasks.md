# 任务与实际状态

前置设计：@docs/changes/20261115-external-skill-methods/design.md。

职责：root 负责需求/设计、整合与受保护交付；`external_core_methods` 和 `external_domain_methods` 按下表实施；`external_independent_review` 保持只读审查。实现者不得修改合同；遇到新缺口先交还 root 修订。

| ID | Owner / 独占写集 | 状态 | Verify |
|---|---|---|---|
| T1 全部 Skill 与原始外部来源对照 | 两组研究，root 汇总证据 | 已完成：65 唯一身份、143 阅读路径，17 原始仓库及 10 项工具依据 | 两组阅读路径与 SHA 对齐基线及 Manifest，65 唯一身份，逐项决定；固定原文路径/版本并说明未取到材料 |
| T2 兼容迁移、独立 oracle、checker 校准 | core：`adk-task-breakdown`、`adk-test-strategy`、`adk-verification-before-completion` 的正文/既有 references；`tests/test_external_core_methods.py` | 已实现并冻结：新增 8 项真实导出/行为/路由测试通过 | `python3 -m unittest tests.test_external_core_methods -v`，真实迁移顺序、错误变体及 checker 对照；定向原有 Skill 契约 |
| T3 性质/状态测试、sanitizer、stack | domain：`adk-unit-test-embedded`、`adk-systematic-debugging`、`adk-static-analysis-c-cpp`、`adk-performance-profiling-embedded` 的必要正文/自身 references；`tests/test_external_domain_methods.py` | 已实现并冻结：新增 4 项通过、0 skip；原有及相关回归 65 项通过 | `python3 -m unittest tests.test_external_domain_methods -v`；真实有界序列回放、GCC UBSan 与 `.su`；无工具明确未运行 |
| T4 接入现有测试与版本 | core 独占 `tests/test_skill_content.sh`；root 用既有版本管理入口同步元数据 | 已完成：94 项内容测试，11.3.4 同步后 8 profile、strict、release check、format、安全与 product-maturity 通过 | 两模块进入现有组；`bash tests/test_skill_content.sh`、原有 8 profile ratchet、strict、`release check`；无阈值放宽 |
| T5 冻结全量验证与独立审核 | root / reviewer | 前两次冻结分别为目录投影 2 pass / 1 fail、完成入口字段 98 pass / 1 fail；原记录保留，修复后待第三次完整重跑及正式审查 | `bash tests/run_all.sh`；源码/证据摘要和实际时间；独立 Spec/Quality、review-evidence 校验、最终树 product-maturity/内容与敏感信息检查 |
| T6 受保护合并与 canonical release | root | 待验证和审核 | exact HEAD 必需检查、正常 squash、main CI、annotated tag、正式 release 和上传制品状态 |

未运行任务不得改写为已完成。原始研究与失败证据先保存在隔离 scratch，公开版本只保留必要且经过检查的内容；加工/脱敏必须注明，不冒充原始字节回执。

合同在实现前已通过独立审查，原审查文件绑定当时四份文档摘要；此表随后按真实进展更新。最终冻结全量、正式 Spec/Quality 与远端交付由后续验证/完成回执记录，不回填原审查时间。
