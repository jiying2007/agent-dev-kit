# 负向发现及证据边界

1. 原 receipt 普通解码接受重复 schema 且通过 decoded digest；rg exit 2 被忽略；维护 summary 报 apply1 但未执行。相应确定性负例已进入 test_contract_hardening。
2. 独立设计审查指出 static symlink/regular 检查与实际 open/scandir 间有竞争替换空窗；新增 descriptor 绑定、NONBLOCK 和目录 inode 检查，测试在真实 open 前替换链接/FIFO/目录链接，验证不跟随、不阻塞。
3. 首次冻结 whole-diff 复审指出 reader 4 MiB 限制没有 producer 闭环：约 8000 文件的合法 plan 可小于预算，而 receipt 大于预算，安装成功后无法读取/回滚。原冻结 source f516a92d8fbb77f93b1b9ea07f69cb460eb88f167dd573fdacd91aa822159215 的矩阵被取消；不将该运行当修复后 PASS。
4. 修复使用相同 encoder/reader 预算，输出计划先校验、receipt 先做保守上界预检再部署，实际 receipt 发布前再校验。边界测试覆盖恰好 4 MiB receipt readback、超过一字节拒绝且不创建 plan 输出目录、超限 receipt 预检不创建资产目标。正常安装/rollback 仍由原 test_install 检查。

上述为源码/fixture 证据；未调用真实模型，不代表新版本签名发布、live 采用或当前 M5 资格。
