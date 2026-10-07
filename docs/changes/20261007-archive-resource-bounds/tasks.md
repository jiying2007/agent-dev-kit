# 阶段与恢复

- [x] baseline/root/SDK dirty核验、Provider explicit route、当前thread新逻辑目标登记。
- [x] 内部资源缺口复现、真实制品尺寸与外部一手资料。
- 实施验收：bounded snapshot/解压reader/critical member与actual extraction入口；非交互确定性测试。
- 验证验收：定向、实际旧制品兼容、三Python full parity、whole-staged独立复审。
- 交付验收：exact head SCM/main CI/immutable artifact/signature读回；Root原子消费、完整回归与复审；Provider reviewing与final gate。

owner=主Agent；kind=implementation；权限沿用实施/SCM授权，禁止真实模型和用户dirty覆盖。shared源码/index在验证前冻结，共享输出串行。retry_budget=2；heartbeat=每阶段实际进展并登记；staleness_threshold=30分钟；两个Major类连续出现时replan；stop_condition=pass/replan/blocked。
控制goal：task-c70d6fce656f511993575765；验收来源审查与明确预算contract；不将source conformance推为产品资格。下一步：实现与定向→freeze完整验证→实际交付。外部预算/线程验证不可伪造。
源码阶段当前记录：20archive/14JSON及实际8.0.3digest兼容通过；19path independent source reviewPASS。quick功能56/56但墙钟预算与正式baseline均超限，保留负结果；不为此放宽performance manifest。final full receipt /tmp/adk-804-final-archive-full-20261007.json 必须绑定实际freeze source/index并check-receipt，不预填成功。SCM/Root消费/Provider终态单独读回。
