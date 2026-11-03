# 有界交付检查点

- [x] 静态审查：7 个 workflow 前后阶段比较，定位 skill-curation package 多于声明；核实完整 66 Skill/13 Agent/8 Profile 的 Manifest 基础注册。
- [x] 实施：Workflow IR 严格序号与完整列表校验，以及 Skill Curation package 绑定。
- [x] 实施：Driver 实现/Bring-up 路由及过宽触发词的最小收敛、SKILL 版本同步。
- [x] 实施：Python3.8/3.11/3.12 的 PR 版本提前失败；保留 aggregate 必需质量检查。
- [x] 增加针对上述变化的正/负例及回滚边界。
- [ ] 独立 reviewer 实际阅读整份 8.2.1 候选后写当前 source-bound Spec/Quality/Harness 七维证据；不得复用 8.2.0 审核。
- [ ] 精确 PR HEAD 原生必需 CI/安全/评价全部 PASS；GitHub 正常 merge，fresh-main CI 和 immutable 8.2.1 Release 真实签名发布。
- [ ] 若新 ADK 完整发布，Root 经 canonical promotion 精确锁定 8.2.1，再核 Root 全部门禁和 fresh-main；历史 M5/field 状态独立不继承。
- [ ] 实际 Skill 使用率/错路由率/Token/延迟的 A/B 收据只有真实运行时才可填写，目前 UNKNOWN；没有确认消费者时不硬删 Python3.8/v1 schema。

边界：本文件不是部署记录或签名证书。当前执行事实以 GitHub commit、Jobs、Artifact 和独立审核记录为准。
