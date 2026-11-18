# 构建入口单一解释器策略：需求

## 问题
ADK `devkit.sh` 已强制 CPython 3.12，但 `version-manager.sh` 的 current、verify、sync、compare 仍直接选宿主 `python3`。宿主使用 Python 3.10/3.11 时，与已激活的 Python 3.12 虚拟环境及版本工具链发生分歧。原探测的进程替换路径还可能丢失解释器的非零退出。

## 验收
- 两个入口复用相同选择顺序：显式 `ADK_PYTHON_BIN` > 当前虚拟环境 > 自动优先 Python 3.12；旧解释器拒绝执行，不静默降级。
- 纯 shell 的 `version-manager.sh --help` 和 `unlock` 行为保持；已有用户命令和退出码语义保持。
- 通过原 Python launcher 回归、版本身份、全量 CI 和 exact-head 发行门禁验证；不碰部署后的 Skill 消费运行时与 Root 产品资格。
