# Python 构建入口收敛

问题：本地 CI parity 与 auto-ops 中导入 ADK Python 模块时仍直接使用宿主 python3，与唯一 CPython 3.12 管理基线和 11.4.6 入口契约不一致。

验收：仅导入 ADK 核心模块的分支复用唯一选择器；保留 dry-run、shell-only 和 apply 拒绝写入行为；不得增加部署后纯 Skill Python 依赖。原 CI、Release、Root 消费均独立验证。
