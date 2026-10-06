# 安装文档安全发布设计

复用 installation_contract 私有 writer：NamedTemporaryFile 同目录随机名、exclusive creation、descriptor 写入、flush/fsync、关闭、os.replace。不再跟随 output leaf symlink，不删除旧固定 `.tmp`。使用 Python 3.8 可用参数，不引入依赖或 runtime fallback。

计划和回执保留 `_encode_document` 的预算前置以及实际 receipt 出版预算。安装失败沿用原有 reverse deployed / moved backups 恢复，临时文件由 writer 单独负责。新计划与 receipt 在 POSIX 发布为 0600，适用于当前安装用户；不承诺 group-readable，多用户共享读取应由明确的部署权限流程管理。Schema/API 保持，安全修复拟 patch 8.0.1。

os.replace 的原子可见性不代表父目录 fsync 或断电后整个安装事务恢复；调用方仍须控制目录和写入者。输出的 symlink 或特殊文件被明确拒绝，父目录并发不在本次保证中。

依据：[Python tempfile](https://docs.python.org/3/library/tempfile.html)、[Python os.replace](https://docs.python.org/3/library/os.html#os.replace)。仅官方设计证据，不导入外部源码。

回滚基线 2c5bd3574c660c5d71bd7e71502977f8cadcf0ad；回退此安全修复会恢复已证明的固定临时路径风险。source/CI/真实发行与消费者 pin/source-to-live 分开验证。
