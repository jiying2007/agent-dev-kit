# 负结果与环境边界

| 日期 | 假设/检查 | 结果 | 决策 |
|---|---|---|---|
| 2026-10-20 | 检索 `knowledge/L2-domain/lessons.md` 的 install/rollback/source 历史教训 | 文件不存在；目录内只有其他领域索引 | 不虚构历史经验；本变更由已复核源码路径和新增确定性验收驱动 |
| 2026-10-20 | 初始环境可直接执行仓库 rtk 和 Provider 门禁 | 初始缺少 rtk 与审查 runtime；随后主任务从官方来源安装并校验 rtk 1.0.1 | 后续 shell/定向验证使用真实 rtk；审查 runtime 仍缺失，不声称 Provider 门禁通过；本地验证与真实 PR CI 分别记证据 |
| 2026-10-20 | 文档中的 Python 3.11 是独立发布工具链门槛 | launcher 严格门槛与 doctor 均为 3.8，原生迁移合同包括发布命令 | 修正当前使用文档；保留历史 change 记录原文 |
| 2026-10-20 | 新正向 rehearsal 测试读取 build 结果键 `archive` | 首跑 7 个 installer 验收通过；release 测试在读取结果时 KeyError，实际合同键为 `artifact` | 查验 `build_release` 返回合同后只修正测试字段；此轮不记 release 验收通过 |
| 2026-10-20 | release 回归脚本存在 `ROOT_DIR` 变量 | 新正向用例单独已通过；挂接脚本在既有 26 个用例通过后因未定义变量退出 | 复核该脚本以 repo cwd 为合同，改用与既有调用一致的相对测试路径，不改变断言 |
| 2026-10-20 | managed mode 校验器的静态参数 `str` 覆盖实际 JSON 边界 | 对 7 个受影响模块执行严格 mypy，4 处 JSON `.get` 输入为 `Any | None` | 参数标注改为 `object`，保留原有字符串/八进制/regular-file/权限精确检查；不使用 cast 或忽略错误 |

## 关闭状态

上述测试字段、脚本挂接和静态注解问题均已修正并在原入口复验通过。最终本地完整回归退出 0（98/98），strict validate 与 release check 退出 0；详细命令见 verification-evidence.md。未删除/弱化断言或 Gate，未把 Provider runtime 缺失、真实 Python 3.8/3.11 尚未执行、远端 CI 待执行标记为通过。
