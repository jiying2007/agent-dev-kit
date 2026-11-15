# fix(skills): 改善任务检索、恢复与专业执行方法（11.3.2）

## 为什么修改

用户要求优化全部 Skills 的功能、性能与易用性。当前存在可观察缺陷：声明的任务触发语无法通过 catalog 查回；Goal 只读恢复丢失阻塞/在途信息并拒绝历史 closed/blocked 批次；若干专业示例混淆验证层、吞掉退出码或要求不存在的通用命令。

## 变更

- 对 56 core + 9 optional 的全部 65 项完成任务方法源审查；14 项原有 Skill/references 修复，51 项有具体保留理由；不新增 Skill、运行时或评测平台。
- catalog find 复用正向 triggers，提高按实际任务发现能力，保持类型范围与只读权限。
- Goal resume 完整展示恢复状态和原批次；strict plan-check/render 不放宽，预算示例使用未知值。
- 修复测试设计到已授权实施的交接、简化代码后续清理、API/ABI 证据、RTOS 迭代、性能指标/采样错误传播、头文件 TU 扫描、离线 GDB 及 URL/IMAP 获取方法。
- README/usage 提供任务入口；Pilot 与 Token 检查按实际目标分流；纠正 micro 预算越过路由的误导。现有 profile 体积上限全部保留。

## 验证

冻结源码的全部 102 组回归通过（0 失败）；Goal/planning 37 项、领域/路由/profile 67 项通过，8 个组合体积上限全部保留。独立本地源码 Spec/Quality 均 PASS，未关闭 blocker/major 为 0。定向红绿、真实 GCC/C 反例及 source/hash 绑定见同目录 verification.md、negative-results.md、review-evidence.json 和 evidence/。此文件在远端写入前仅是可审阅草稿，远端 CI 尚未运行。

## 范围与风险

Manifest 除版本外逐值不变。E1 自动化路径仍不可达；真实模型 A/B、Token/费用/时延及板端效果未测。只读恢复不执行输入记录的命令。没有用户运行时安装或设备操作。回退本变更可恢复旧源码行为。合并仍需精确 HEAD 的所有受保护检查；主线 CI 与 Release 是后续独立步骤。
