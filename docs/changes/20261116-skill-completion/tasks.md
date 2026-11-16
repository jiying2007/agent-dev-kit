# 任务与当前状态

设计：@docs/changes/20261116-skill-completion/design.md。

| ID | Owner / 独占写集 | 状态 | Verify |
|---|---|---|---|
| T1 | general/embedded 只读审计；root 汇总本 change 证据 | 完成 65 + 53 路径；7 changed / 58 retained | manifest 精确集合、118 个基线/候选摘要核对，audit.md 与 portfolio-audit.json |
| T2 | research-review 只读外部研究与独立审查；root 归档 | 10 源仓库/14 入口研究完成；设计及分区源码审查通过，总体最终审查待完整回归 | 固定来源身份、许可、采用差异；独立报告和真实复跑 |
| T3 | general：parallel-agent-governance 入口及原 reference；engineering-growth-review 入口/README；archive-governance 入口；optional data-fetch 父入口；code-review-loop 入口版本及 review-feedback-fixtures.md；既有 test_skill_content_contract.py | 五项完成，独立 T3 Spec/Quality PASS | 同一测试 5 RED→GREEN；旧 content/method 24 PASS、SOP/预算通过；真实导出/Git；4 个新上下文任务产物与14输入不变证据 |
| T4 | embedded：cmake-cross-build、integration-hil-sil 入口；test_skill_command_examples.py | 实现完成，独立 11 方法定向复核通过；旧5个Ninja用例留待CI | Make8真实执行、XML15子场景、fresh JUnit/partial；37方法32 PASS/5本地缺Ninja skip；不以Make替代多配置 |
| T5 | embedded：test_skill_command_examples.py 的 run_example 与回归 | 实现完成；真实默认15秒RED/GREEN及独立隔离进程组复核通过 | 两流、身份、work/cleanup分开；本组终止、另一组存活；脱组持管道路径有界返回 |
| T6 | root 集成：11.3.7版本投影与原未执行AB计划候选版本、生成catalog、合同、完整证据/提交；research-review独立只读 | 原8 ratchet、strict/security/SOP已过；完整提交回归与最终裁决待执行 | 不改AB基线/cases/holdout/results/not-measured；完整tests/run_all.sh与最终source/hash绑定 |
| T7 | root 平台交付 | 待源码验证与独立裁决 | 精确 HEAD 的 PR CI、正常 merge、main CI、不可变 tag/Release/asset digest |

当前角色：root 集成；general/embedded 实现停写；research-review 独立只读；新上下文执行者仅完成指定四项结果，没有继承诊断/修复上下文。最多三个下一动作：冻结源码并跑完整回归、最终独立裁决与证据封装、普通 PR/main/Release 闭环。

环境：本轮实际 `command -v rtk` 无结果，使用原始命令；`knowledge/L2-domain/lessons.md` 不存在，负结果见同目录记录。不把缺失工具记为通过。
