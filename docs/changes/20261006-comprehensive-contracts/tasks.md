# 任务与分阶段证据

- [x] 冻结 canonical 基线、目标、风险和验收；保护主检出及用户 dirty。
- [x] 将安装计划/receipt 接入 strict JSON，补叶节点常规文件 descriptor 检查。
- [x] runtime-boundary 扫描失败闭合，规则与 glob 保持一致。
- [x] 维护工具改为有界只读候选，退役无审查 --apply；修复 report written 声明。
- [x] 补 JSON、叶节点替换/FIFO、目录链接替换、预算和实际 CLI 回归；初始本地定向 10 个测试通过。
- [x] 独立设计复审发现 TOCTOU 与 MAJOR 迁移问题；实现修复、明确非原子快照及父目录边界，并将完整候选标为 8.0.0。
- [x] 首次冻结复审发现 producer receipt 无预算可能写出 reader 无法读取的文件；增加输出预算、资产写入前保守预检和实际 receipt 再校验，以及边界/readback 回归。旧快照矩阵取消，其结果不重标为修复后的证据。
- [ ] 冻结索引后进行完整测试/支持 Python 矩阵和独立最终复审。
- [ ] 实际提交、托管检查、合并和发布签名读取；不得提前填写完成。
- [ ] 消费者 exact 来源升级、build/doctor/plan/dry-run/apply/check；不得提前填写完成。

最终阶段证据写在 source 外的交接文件，避免回归完成后改写本文件造成 source snapshot 漂移。M5/真实模型和产品/owner 资格保留独立门禁；无真实模型调用。
