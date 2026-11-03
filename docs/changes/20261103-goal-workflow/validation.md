# 验证与交付边界

2026-11-03，review_target=working-tree；reviewer_independence=author-self-review。未提交、未推送、未操作设备。自审不授独立审查或产品资格。

## 实现与实际验证

| 项目 | 新鲜证据 |
|---|---|
| ADK状态兼容 | planning_state 3项单测通过；真实GROS GOAL-CURRENT含work_in_progress回读pass，completion_allowed=false |
| Codex入口/合同 | goal_plan/operator_execution_policy/execution_policy/check_skills共36项通过；调用cwd含恶意同名tools的遮蔽负例通过 |
| 技能格式与发现 | 官方quick_validate通过；default检索goal-authoring为deferred/lazy，常驻数保持12 |
| gros_compile试点 | 56原父标识=9个P包+47个V项；12个交付组，当前仅SW-AAC。状态1442字节，resume输出2404字节；结构通过不证明语义/业务完成 |
| 隔离安装候选 | 587项Python测试0失败0错误；完整check通过，包含repo/build/live/governance、deny-path、sandbox、四profile smoke、最终diff/drift |
| 实际安装 | 5 copy+2 overwrite，0 delete；仅Goal技能、registry及managed state；当前team-collab和activity-report1.0.0/session-wrap4.0.1保持 |

技能为local/codex的goal-authoring0.1.0，未手改外部ADK镜像。ADK状态兼容是本地源码候选，未声明新的签名上游发布或全量受管导入。

## 来源与回退

Codex人工源在其src/codex-home/vendor/skills/goal-authoring/0.1.0，工具在tools/codex_assets/goal_plan.py，跨cwd入口在entrypoint.py；gros_compile使用docs/plans/f10-f20-current.json作为唯一动态入口。

因为Codex源仓还有无关activity-report1.1.0/session-wrap4.1.0草稿，本轮隔离候选仅保留这两项live版本，不覆盖原草稿；没有宣称整份源仓已同步。

受管安装证据为本机/tmp/codex-goal-runtime-20261103/apply-plan.json；plan SHA256=69aa32c953612f775e395cfa99360befd618724fd48fcac1d79bf92a2e377d95，source fingerprint=17f9ee21337682c02692480c6abd67a5ca3f5a65b8b632e99d28df8afb80475a。live SKILL SHA256=ca21dade7e4a4a068725c5c26f7609ddd6f85b3b66518df634fad8bad40fd926，与人工源一致。临时安装材料不作为跨仓公共契约；回退需保留候选及该plan绑定的.backups目录，通过原rollback工具执行。

## 扩大门禁负结果

- 原Codex working tree首次全量587项有7个失败记录；更新本次Profile计数后定向剩3个，涉及原有activity-report/session-wrap草稿版本及registry。安装候选保留live版本，补齐快照遗漏schemas后587项全部通过；不修改原仓无关草稿或声称其全绿。
- ADK本机full执行101组：89通过、12失败。明确因素包括OpenAI来源审查过期、MCP来源审查过期及变更后委派审核失效；其他workflow/integration/performance失败未逐项归因，不能断言全部既有或已修。
- 支持版本Docker parity因3.8/3.11/3.12镜像缺失而未执行；本机根回归要求Python3.11+而实际为3.8。
- 根quick工作树检查已报告ADK锁8.1.5与源码8.1.1不一致、来源过期、缺cosign及Python版本问题；后续reference-source-integrity扫描长时间无新输出，核准本轮进程身份后终止，仅此检查进程组。该门禁未全通过。
- 技能检查有1条缺少独立LICENSE文件的包装warning，没有校验error。未声称对外开源分发资格。

## 未关闭与度量

原业务Goal保持usage_limited，未恢复、替换或清零；AAC及全部V项仍未完成。1000000-token批次预算只是提案，未设置宿主预算。需要在原线程按公开宿主能力继续。

技能模型行为eval、真实任务A/B token收益及fresh independent语义审查未取得。当前仅证明文档有界、确定性工具行为与有界运行安装。后续量测每关闭子项tokens、恢复至首动作耗时、无变化重跑和整体final次数。

Codify Decision：reusable_pattern=父验收到有限批次和有界恢复；promotion_candidate=false；next_task_friction_reduced=恢复材料与跨cwd入口；reduced_by=状态外化和固定import root；reduction_evidence=1442/2404字节及shadow-package负例，非token收益；do_not_promote_reason=缺模型eval/独审/真实A-B；owner_review=未执行；rollback_path=同受管plan及备份；verification_evidence=本表。
