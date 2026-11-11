# Goal Skill 精简与路由负例（11.2.3）

## 变更边界
- 主 Skill 仍只有 `adk-goal-authoring`（新建/实质修订合同）与 `adk-planning-execution-loop`（执行批准计划），不创建第三套 Goal/runtime/预算治理。
- Goal 执行不再由“长任务”“计划审查”“恢复摘要”这些宽泛短语触发；只读 CI/等待状态交确定性 Host，不进行无变化模型轮询。
- 使用已有 `references/long-task-recovery.md` 保存高风险、恢复、独立证据、并行资源和 stop gate 细节，仅在触发时读。
- `goal_plan.check` 允许 `budget_proposal.tokens=null` 并须保留非空 basis 和 `native_goal_applied=false`，不以编造正整数 Token 预算通过校验。不影响真正 Runtime Budget。
- Skill 不签发批准、不能变更原验收分母、不能自行恢复被宿主限制的 Goal，不创建定时任务。

## 源码体积基线（精确字符数，非 provider Token）
| 文件 | 11.2.2 原值 | 11.2.3 候选 |
|---|---:|---:|
| Goal Authoring SKILL.md | 2018 | 1606 |
| Planning Execution SKILL.md | 4533 | 1793 |
| 既有恢复 reference | 1109 | 2417 |
| 合计 | 7660 | 5816 |

主入口两份合计从 6551 降至 3399（减少 3152 字符）；加上按需恢复 reference，合计减少 1844 字符。该数字来自源码长度，不是 Tokenizer/缓存/模型效果实测，也不意味着 runtime 初始上下文必然下降。Profile 既有 source-growth ratchet 不放宽。

## 验证和边界
- `tests/test_skill_trigger_matrix.py` 与 `tests/fixtures/skill_trigger_cases.tsv`：新建与继续执行正例、只读 CI、计划审查、摘要请求、已有目标误触发负例。
- `tests/test_goal_authoring.py`：未知预算 `null` 合法、0/负数/布尔/字符串非法、不能谎称 native budget。
- 既有的 `tests/test_goal_convergence.py` 保证原验收、evidence-bound 进展、replan、milestone/final 权限边界不回退。
- 此轮不在付费 Runtime 上执行真人/真实模型 A/B；真实 discovery/load/trigger 与 Token/里程碑效果仍为 NOT_EVALUATED。Codex vendor 和用户目录不直接编辑，必须通过发布后受管源导入核验。

## 发布
原 immutable v11.2.2 已发布，候选源码版本前移 v11.2.3；需在受保护 main 的真正 CI 成功后按 canonical release-tag-promotion 的 exact SHA 交易发布。若发布/签名/审核证据缺失，明确阻塞，不用人工改旧 tag 或直接更新消费方 pin。
