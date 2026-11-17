# 验证与交付边界

本轮落实 65 项 Skill 审查中的 5 个明确问题与 3 个条件性方法补充。候选版本为 11.3.13；具体实现及测试来源由 review-evidence.json、evidence/original.patch 与源文件摘要绑定。

## 已完成的源码改动

| 范围 | 改动与结果 |
|---|---|
| 嵌入式单测 | 可选 implicit_context 由既有 canonical matcher 消费；通用单测退出，MCU/RTOS 及其 Python/Rust host 模型保留；正常行内格式化技术名保留；显式诊断与写入权限仍分离。 |
| perf | 通用 cache-misses 不再被标为通用 LLC miss；按目标 PMU/内核核对事件，LLC 使用已验证的对应事件。 |
| artifact-gating | 独立消费者使用已核项目门禁；Root 专属 helper 只适用于真实 llm_agent Root 接入；适用门禁缺失仍阻塞。 |
| composition | 真实递归 rg 扫描覆盖全部 65 个入口，包括两个嵌套 optional Skill。 |
| growth | frontmatter 与正文统一，长期 prompt/Skill/Workflow/AGENTS/记忆规则才进入晋级链；普通建议不需晋级，实施仍按原授权。 |
| URL | 实际连接地址、重试/fallback/重定向受已核地址约束，保留原 hostname 的 Host/SNI/证书验证。 |
| UBI/UBIFS | 目标与镜像几何参数适用时逐项核对；未知或不一致保持 host 级检查。 |
| 多人试点 | 区分 human-active 时间并集与多人合计 person-minutes，比较使用相同口径。 |

## 实际验证

- 独立 source-change 审查：Spec PASS、Quality PASS；Q-01 测试盲点、R-01 格式化目标回归、P-01 候选版本遗漏均经修复与独立复验。
- 路由矩阵 21/21；独立邻域正反控 22/22，全部 mutation_permission=deny。原成功路径与显式否定/引用示例反控均有记录。
- 方法测试包含真实递归扫描与两种 team-core compiler 导出；不能将源方法检查等同于现场设备或真实网络客户端运行。
- 原 8 个 Profile ratchet 全部通过；阈值和计量器逐字不变。65 个 Skill 身份保持；8 个入口净减少 216 B，计入两个参考文件后净减少 71 B。
- 本地完整回归第二次实际为 102 套中的 101 套通过、1 套失败。唯一失败为未执行评测计划的候选版本未同步。最小 fixture 修正后重跑完整失败 suite，204/204 通过；另有独立原失败单项 1/1 通过。其余 101 套按唯一 fixture 差异复用；本记录不声称新的本地完整 102 套通过。
- 首次完整回归因独立审查发现路由回归而中断，exit 130；中断和第二次失败均保留原始记录。
- strict validation、版本一致性、格式、模块规模与目录生成检查通过。本地未安装的 Ruff/mypy/pip-audit 由既有受保护 CI 执行，不标成本地已运行。

## 发布前后闭环

源码审核目标 66df0ce7092aabbbd05411ef2950cc9ee59a3592 的 tree 为 081cddd941f16a98aee76014998856bd33799610。通过已连接 GitHub 接口传输后，已核完整 tree 和原始差分与本地源一致。证据包装需单独增量审核；最终精确 PR/main 必须通过完整所需 CI 后才进入现有自动不可变发布链。

Root 仅在不可变 Release 真实可核之后更新 agent-dev-kit Gitlink 与 reports/current-status.md 自动块。native Release digest/attestation 沿用已有 integration-deep 检查；不改写历史 M5、Harness、runtime 或 field 资格。

Goal continuation 保留一次真实当前任务的新上下文恢复观察：验收、owner、依赖及未完成状态保持，没有重复分派或虚报任务完成。该观察不属于配对 A/B 或原生宿主认证。provider usage、Token、成本、真实 PMU、UBI 写入、DNS 客户端与现场效果均未测，不由字节变化或本地确定性测试推断。

回滚使用前一不可变 11.3.12 与原 Root Gitlink，不覆盖发布 tag。最终发布/接入结论以对应 PR、精确 CI 与 Root 状态投影为准。
