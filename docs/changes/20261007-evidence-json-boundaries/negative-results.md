# 负结果与复审修复

- 初次 shell 测试单独执行未使用 suite 的 Python 环境：`python` 指向 Python 2 导致 encoding 参数错误，另一入口没有 PYTHONPATH；不计源码失败或通过，改用隔离 local CI 正式入口。
- 首轮三 Python parity 在 distribution 两处 import 排序处失败；没有回归通过 receipt，结果仅作为负证据，修复后重新跑完整矩阵。
- 首次独立复审提出两个 Major：ensure_within 提前 resolve 使真实契约/原生回执入口叶链接检查失效；receipt 在预算前无界 read_bytes 且 hash/parse 两次读取。已修复为 lexical 路径+root 检查、有界 descriptor 单次读取字节；新增公开调用链测试。
- 首次矩阵源 aa830f7df189eb2e5e0c17b0371d4d5a4b4bcd72a199d855a119b87159ab544b 已过期；不能用于最终源通过声明。
- 第二轮未暂存 index 的矩阵只作过程证据；为冻结源码和 Git index 身份，受控终止本任务 runner1032662及其唯一容器2e6c8fc8a429。未清理其它进程/目录；进度日志保留 /tmp/adk-803-prestage-matrix-progress-20261007.log。最终验证重新运行冻结 staged 包。
