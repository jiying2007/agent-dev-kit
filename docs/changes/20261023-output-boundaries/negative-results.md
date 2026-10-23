# 负结果与执行边界

- 2026-10-23：`knowledge/L2-domain/lessons.md` 不存在；未发现可加载的历史教训文件，不伪造知识来源。
- 新增行为回归先在未修复实现运行：export 5 tests 中失败 5 个子断言、2 个后续 fixture 错误；Native 8 tests 中失败 11 个子断言，包含原本接受 FIFO、覆盖同路径、先写第一输出再失败及无批量恢复。原始结果见 `evidence/regression-red.json`。
- export 的后续 fixture 错误由旧实现未拒绝链接、删除哨兵及保留 alias 导致；独立正向替换与原有单目录恢复控制通过。
- 只使用隔离本地无害 fixture；未调用真实付费 runtime，不生成签名、现场事件或产品资格。
- rtk 使用经主 Agent 核对的官方二进制，Python 使用隔离 venv。`~/codex` 与 Execution Policy 不在此环境，未声称通过。
- 扩展 finalize 硬链接回归首次试跑遇到 EXDEV：本环境 `/tmp` 与仓库位于不同文件系统。将硬链接的两个端点放入同一个隔离 runtime-report 目录后复验；没有跳过硬链接断言。
- 四个目标模块的 mypy 首轮指出新列表索引的 Optional 窄化不足，以及既有 finalize 声明返回 dict、实际 deepcopy(Mapping) 的类型不一致。分别改用局部变量窄化与显式 dict 副本，未弱化类型检查。
- Native 既有 exited-launcher pipe-drain 单测会输出 asyncio unclosed transport / Event loop is closed 的 ResourceWarning；当前输出修复不涉及 executor，已向主 Agent 报告，不能声称该资源清理告警已关闭。
