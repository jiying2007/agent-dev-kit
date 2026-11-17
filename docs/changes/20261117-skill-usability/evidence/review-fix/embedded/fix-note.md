# U06 终审回归修复：VxWorks

仅修改 `skills/adk-rtos-task-design/SKILL.md` 的现有 `implicit_context`，追加 `/VxWorks`，增加 8 B。保留原 RTOS/Zephyr/ThreadX/RT-Thread、排除词、RTA 方法与未发布的 Skill 2.0.4 版本；没有扩大为通用 RTOS 分类器。未修改共享测试或任何 ratchet。

## 原始问题与验证

终审原始证据为 `/workspace/scratch/fe8de3b42084/skill-usability-review/review-probes.json:routing[8]`：`请为 VxWorks 做任务设计` 在基线选中 RTOS Skill，在首轮候选 abstain。

本次 `verify_vxworks.py` 直接调用生产 matcher，固定四条验收：VxWorks、FreeRTOS 两正例，季度销售任务、明确没有 RTOS 的裸机任务两负例；四条均要求 mutation permission 保持 deny。

- RED：3/4 通过，唯一失败为 VxWorks 原正例；`red.json` 保存原始结果，命令 exit 1。
- GREEN：4/4 通过；`green.json` 保存完整 matcher 结果，命令 exit 0。
- 8 个现有 profile ratchet 全部通过，policy 文件 hash 前后相同。`large-refactor` full 为 `323306 / 323328`，剩余 **22 B**；`embedded-fullstack` 为 `316424 / 316854`，剩余 **430 B**。其余六个 profile 也通过，完整数值见 `summary.json`。
- `git diff --check -- skills/adk-rtos-task-design/SKILL.md` exit 0。
- 已将 VxWorks 正例及既有两负例交给 audit_workflow，由其维护唯一共享测试。

源文件修改前 SHA256：`d087ee87d5b513e82319045ccbf1952f2f62764831e1ad6681263df730713f7a`。

修改后 SHA256：`67658d3a4f029dcbd86c6a6eba76870d588bbfc61275152b0e72b233edb8e803`。

通过把当前正文这一行换回原行后重算 hash，确认本轮源文件只有这一行变化；局部差异保存为 `change.diff`。原 T3a 审查及实现证据保持不变。

## 复现

```bash
/workspace/scratch/fe8de3b42084/verification-tools/rtk python3 -B \
  /workspace/scratch/fe8de3b42084/skill-usability-audit/embedded/review-fix/verify_vxworks.py green
```

本次只验证局部生产 matcher 与源字节；没有原生 Agent runtime 或设备运行。先前全量回归由协调者停止、exit 130，不是全套 PASS；本修复没有启动或冒充新的全量结果。未 commit/push，RTOS Skill 文件已可交还集成与独立复审。

Build 前 `knowledge/L2-domain/lessons.md` 仍不存在，记录该检索负结果。
