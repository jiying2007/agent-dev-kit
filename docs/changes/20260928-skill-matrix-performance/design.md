# 设计

Shell 入口只转发到 Python unittest。测试加载一次 Manifest，按原 TSV 顺序调用 `agent_dev_kit.matcher.match_text`，比较布尔结果；另用一个已知通过的样例调用真实 `devkit.sh match` 检查 CLI 封装。数据列数、标签和 scope 无效时 fail-closed。

此变更只优化测试进程边界；外部 provider、runtime eval、发布证据和 source-to-live 均不受此测试通过结果授予权限。
