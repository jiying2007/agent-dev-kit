# 独立合同审查：外部 Skill 方法增量

- Reviewer：`external_independent_review`，只读角色；未参与需求、设计或实现编写。
- Change：`20261115-external-skill-methods`。
- 实现基线：`5e0e83bcc127665de9a352e9eacfe9b092106cb2` / v11.3.3。
- 审查完成时间：2026-11-15 13:52:51 UTC（运行时 clock）。
- 结论：**PASS，可开始 T2/T3 实施**。阻塞项 0；必须修改的合同缺陷 0；实施核验注意项 3。
- 本结论只覆盖下面绑定的合同内容，不代表尚未出现的实现、模型效果、真实宿主行为或发布资格已通过。

## 审查输入与摘要

输入位于 `agent-dev-kit-external/docs/changes/20261115-external-skill-methods/`：

| 文件 | SHA256 |
|---|---|
| requirements.md | `d66a8ccb4e645a4416318261935384c97eec0c1e8e756ccfafd58c4fcefec0ca` |
| design.md | `9567c72b65245fef2652a0c432789b221ecfc06ee11ee68abcfb412e95d8a38e` |
| tasks.md | `7cb47f6fff0d00241b845d4caf5ee227be4cf4ee42b8b969f112a794ec9a7855` |
| negative-results.md | `a3043a35ed5bf30c6244b08300cc79bcef86d47c927ddfd165fe980e886b164e` |

已读四份合同全部内容，并核对现存 `tests/test_skill_content.sh`、七个目标 Skill/reference 的路径、unit-test 入口、memory-footprint reference、先前读取的 target renderer 和仓库角色/验证规则。未执行产品测试，因为实现尚未开始；不存在“测试已通过”的推断。

## 审查结果

### 需求与范围：通过

六类方法均有实际问题、应用条件、目标现有资产、可观察失败与通过条件。全面审查 65 项与实际修改有缺口的七个 Skill 没有混淆；需求明确允许保留已有充分方法。全网检索被准确限定为有界广泛发现与原文核验，未承诺穷尽互联网。

迁移、独立 oracle、checker、property/stateful、sanitizer 和 stack 的验收均能映射到确定性程序、真实工具命令或有范围说明的源码契约。任务列表给出两位实现者的独占写集；core 单独修改共享测试入口，降低并行冲突。root 负责合同与整合、reviewer 保持只读，不把自审当独立审查。

### 可携带性：通过

设计根据实际 `_render_main` 和 `_render_support_files` 行为，将必要约束放正文，将完整方法放所属 Skill 自身 reference。跨 Skill 仅条件性交接，不创建未声明的硬文件依赖。禁止为通过 profile ratchet 而放宽阈值，并要求删冗余时保留失败解释；该约束可机械复验。

### 验证设计与独立性：通过

迁移验证包含过早删除失败与完整迁移成功；独立 oracle 需要真实错误变体与正确边界双向对照；checker 不以 exit 0 充当业务成功。三项均能避免纯关键词或格式存在性自证。

property/stateful 要求外部契约性质、非空有效输入、合法/非法序列与状态重置。sanitizer 以已知缺陷证明插桩实际有效，保留 default recover 的非零业务判读。stack 把函数 frame、调用链和 runtime 峰值区分，避免静态数字扩大为任务栈上界。

完整回归、strict、8 profile ratchet、独立审核、待发布树敏感信息检查和正常受保护合并仍使用现有机制。未增加生产 scanner、运行时、评测引擎或外部依赖。

### 证据边界与授权：通过

合同明确不执行第三方脚本、不进行额外收费模型评测、不操作真实设备；host 例程与源码验证不证明模型收益、板端性能或目标无缺陷。未运行保持 not-run/not-measured，工具缺失可显式 skip 并报告实际覆盖。既有推送/合并授权继续有效，没有重复询权或扩大权限。

## 非阻塞实施核验注意项

这些不是已确认的合同缺陷，也不要求先加新流程；在实现与最终审查中落实即可。

| ID | 风险 | 可执行处理与验收 |
|---|---|---|
| N1 | 独立 toy 程序通过，但最终公开示例采用另一段未验证逻辑。 | 测试运行文档给出的同一命令/代码，或明确对应同一函数/语义与参数；保留原始负例、正确例和合法边界。最终 reviewer 对照测试与公开示例，不能只看测试名称。 |
| N2 | “最小反例”仅是找到的一个反例，未实际证明最小。 | 用有界枚举/删减与重放说明缩减结果；无法证明时准确称“可重放反例”，不要声称全局最小。不得为满足措辞新增外部 fuzz 框架。 |
| N3 | host GCC 只产生部分 `.su` qualifier，却将其作为全部平台覆盖。 | 日志保留实际 compiler、flags、qualifier 和范围；`dynamic,bounded`、IRQ/RTOS、高水位单位等未执行部分用适用官方来源和明确未验证边界说明，不用 fabricated fixture 冒充 GCC 或板端实测。 |

## 后续审核入口

实现完成后重新审查完整 diff、两模块真实运行、现有回归和导出行为。最终 Spec/Quality 需绑定当时的实际源码与证据摘要，并核对完整日志、失败记录和时间顺序；本次合同 PASS 不继承为最终代码或发布 PASS。
