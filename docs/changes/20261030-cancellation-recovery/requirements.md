# 取消期间保留事务恢复材料

## 目标

修复多文件 publication 与 install apply 在 KeyboardInterrupt/SystemExit 等取消路径中清理原始备份或未完成事务标记的问题。

Owner 已在 2026-10-30 审查后授权按建议全部优化落地。

## 边界

保持单文件 rename、锁、普通失败补偿及现有回滚入口；不承诺掉电级多文件原子性，不执行 live 安装。

## 验收

1. 在临时目录验证发布取消后原文件字节仍可从目标或备份恢复。
2. 验证普通成功与可恢复 I/O 失败仍清理材料，取消或恢复中断保留材料。
3. 验证安装中断保留 staging/backup，后续 apply 与 rollback 拒绝未完成事务。
