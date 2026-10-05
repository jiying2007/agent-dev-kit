# 任务

- [x] 拒绝根级和嵌套重复 JSON 键，并增加文件解析负例。
- [x] 固定全回归 cwd，父仓和 /tmp 调用复验；相对输出路径保留调用者语义。
- [ ] 定向 effect trials 与完整 ADK 回归。
- [ ] 复核源码 diff、记录真实阻塞；不得推导模型效果或产品发布资格。

检查点：源码 diff / whitespace 已核对；最终 host full 94/95，唯一失败是 clean-commit runtime bundle 阶段因未提交源码阻断（其源码测试 3/3 通过）。隔离 Python 3.8 full 95/95、routing 30/30 与 audit 通过，其他版本未闭环。根仓 full 68/69，唯一失败 clean-root-source rollover。Execution Policy 返回 stop，本 change 不声明完成、release-ready 或已刷新 live。
