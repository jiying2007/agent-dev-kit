# 残余控制入口收敛

- `version-manager.sh unlock` 直接删除受控版本锁，违反 Manifest/锁/Git 身份不变量；删除该命令与实现，不提供旧别名。
- `backup-rollback.sh restore|rollback` 直接选宿主 `python3`，必须复用 ADK CPython 3.12 选择器，回滚备份创建之前失败。
- 保留 shell-only backup/list/verify、typed restore_archive、档案往返与安全回归；不改变 Root/live 部署或外部生产资格。
