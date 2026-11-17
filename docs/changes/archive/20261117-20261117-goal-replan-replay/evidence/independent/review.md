# 独立 Spec / Quality 审查：历史 replan 重放

审查者 ai/independent-review（/root/independent_review），AI、independent；实现作者 ai/audit_core。协调者负责契约、版本整合和证据包装。审查者未实现生产修复、改测试或放宽要求。

## 裁决和身份

**Spec：PASS；Quality：PASS。** source-change范围内无未解决blocker/major。Base为5f113b8f5ae6f83662d41d99d0907026f4e44c9d；最终产品Head为d01d1bcb7c2f322c342656a95e523fba8b55505e，Tree为4fe0cfa656ad7feeabf1a25daa9012dcfd673ce0。完整累计original.patch为85,582 bytes，SHA-256 52fd79f40d5a6592d646c7897d5af605c32d88e6a3ade2c11e2ad41090affafe。

产品Head和后来追加的change证据是不同边界。22个产品变化文件均与exact Git Head相等；包装冻结在2026-11-17T15:12:48.626606Z，review-input-state的SHA-256为02a5258c6dafb709ba9c4b7281364de3c60bd28da87a8f43cf452fe4b3cb17a0。47份输入库存和后续独立审查输出分别保留，未把新证据伪装成完整回归时已存在的提交内容。

## 已修复的实质问题

发现 c2-historical-intake-replay，major / fixed。独立原输入为A(readonly)→B(implementation)→旧A；第三个事件使用新的event_id。旧实现只和当前attestation比较，错误接受已消费A；原冻结probe baseline exit1，原始观察/输入/合成verifier全部保留。

候选在同一次完整reduce_events历史中维护consumed_intakes；有效goal.started和有效goal.updated/replan均记录消费。exact event_id幂等先执行；已消费attestation的新event拒绝；legacy缺intake不把None加入集合。原goal_id摘要绑定、冲突payload、错Goal/错hash拒绝不变。该局部历史集合不增加持久账本、schema或权限权威。

原冻结输入SHA-256为1bddace1b0edebc3475f8e51f1cd0d9a4878c5e9f0c4b17d6d2bf001a2779d60；原probe为b6f5a02415a3310e12fc554f8d166767bf585709b1469c5bd1ecbe10f8ebfa7d。本次独立原样复验4/4、exit0：旧A有/无verifier均拒绝，最新implementation无verifier仍受floor限制，新C合成正控制接受。原冻结七文件与归档副本逐字节相等；未以实施者新输入替代原反例。

## 控制与实际验证

独立execution-policy25项、target-contract脚本实际exit0。新增正负控制覆盖freshC、exact-event重复、冲突重复、重启后消费、跨Goal、legacy None、错摘要。native verifier的False、异常、1/string/mapping拒绝以及True正控制证明的是既有生产拒绝语义；target trust生产代码没有因此修改。

独立定向探针实际执行于d0d2b2dc7cac3e7e7bb853bc372d4afc9975f6bd，不冒称在最终Head重跑。Git差异证明到d01d只压缩两份AAR文本，C2 Python/tests完全相同。协调者随后在精确最终干净worktree执行full102/102、exit0，2026-11-17T15:03:21.720367Z至15:09:48.688971Z；Ruff、focusedRuff、mypy32源、format、strict、release check、export也均exit0。

独立审核核实两轮各1082个运行源文件before/after及实际worktree一致；所有command log摘要与原文相符。第一轮d0d2为101/102，唯一失败属于AAR footprint，并非C2；保持原失败，未重标PASS。最终两份AAR修复后预算和测试不变。共享最终证据已同字节复制到本change的shared-final，避免依赖相邻change移动前的位置。

## 归档与资格边界

canonical的change内source/evidence使用record相对路径；repository只指稳定产品/政策。冻结input-state、脚本和原source_path表示原观察时位置，归档不应改写历史内容。后来review/archive生成的checklist/tasks/state/history不作为此记录的永久产品不变量。审核脚本的47项库存是审查前历史快照，新增独立输出另有本目录索引。

该修复只保证提供完整历史时的确定性消费检测；截断历史、宿主准入/撤销、worker lease、外部commit/ACK及副作用no-replay仍需真实宿主证据。合成verifier不证明实际宿主曾被绕过；默认无verifier路径此前就保守，不能把本修复描述为已认证的真实权限加固。

没有模型/真实native/设备/live安装，未测量模型效果或成本。Provider与宿主不可用仍为UNAVAILABLE/NEEDS_REVIEW；不替代现有authority。本PASS不预认远端CI、merge、Release、Root晋级或宿主final gate。回退该补丁会重新暴露已记载的重放缺口，必须保留该事实，不覆盖tag或原始反例。
