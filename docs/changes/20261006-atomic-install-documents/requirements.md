# 安装文档安全发布需求

8.0.0 的 install plan 与 receipt 固定 `.tmp` 名称可被预置符号链接，导致外部文件被覆盖及 active receipt 不可读取。修复集中于这两个生产者，不调整安装 schema、profile 或来源信任边界。

验收：同目录独占创建随机临时文件；通过创建时 descriptor 写入，flush/fsync/关闭后原子替换；仅清理本次创建的文件；先执行已有 strict JSON 输出预算；预置旧 temporary regular/symlink/FIFO 和外部目标保持；写入、同步或 publication 失败保留旧文档及事务资产。保留可读取、可回滚的实际安装结果。

调用者控制父目录；不声称防御同权限任意并发 writer、父目录 rename 或断电恢复。Python 3.8/3.11/3.12 必须通过完整支持矩阵。模型收益和 owner/M5 资格独立，禁止虚构。
