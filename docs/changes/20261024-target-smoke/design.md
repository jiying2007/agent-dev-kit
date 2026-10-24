# 设计

优先复用已有 native campaign 有界执行能力，将底层进程预算 owner 收敛为可共享实现；smoke 与 native campaign 各自保留业务结果映射。统一总体 deadline、stdout/stderr 合计字节预算和 POSIX 进程组清理，包含直接子进程退出后仍被后代持有的管道。

实现范围为 `targets.py`、必要的 native execution owner 和定向回归；不修改根 manifest、schema、CI、版本或其他发布逻辑。公共接口变化先检索全部调用点。回滚为上一正式版本。

历史 lessons 路径缺失，已记录负结果。隔离环境无声明的 Knowledge Provider 与 Execution Policy，记为环境 not-run；不把本地受控 smoke 当作 Native 或 live 资格。
