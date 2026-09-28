# 设计

- `src/agent_dev_kit/completion_coverage.py` 提供纯函数审计和 `python -m` CLI。输入 JSON 有 1 MiB 预算且禁 symlink；时间以调用方显式 `as_of` 判定，避免测试依赖系统时钟。
- 只接受封闭字段和三种观察状态。`passed` 要求 exit 0；`failed` 要求非 0；`skipped` 只表示有理由未执行。必需项缺失或跳过、任意失败或过期都会得到 `needs-fix`。
- 审计不能证明命令确实运行或证据摘要对应真实文件，因此结果始终 `completion_allowed=false`。与现有 Execution Policy 的 Goal/authority 决策独立；不增加 hosted 服务或写 live。
- 在现有验证 Skill 的按需参考中给出最小调用方式，入口仅保留一句决策边界；使用确定性单位测试和薄 shell 测试纳入 ADK 回归。
- 源码体积棘轮按当前工作树实测：七个包含验证 Skill 的 profile 入口各增加 138 字节、潜在完整源码各增加 781 字节；`incident-response` 不包含该 Skill，基线不变。前者不是 provider token 测量。

回滚：移除模块、测试和 Skill 引用即可，无状态迁移。
