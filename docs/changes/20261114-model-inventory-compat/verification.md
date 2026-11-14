# 模型清单兼容性验证

源码固定为`86710516da820dc112f8126298aa23ab5d2d502a`，tree `4fae75d73e88141cdd8696a9fb377ad5c00fe8df`。完整回归启动时本地HEAD仍为D，但工作区与index为已绑定E的准确tree；全过程保持源码不变，回归结束后才同步本地HEAD。远端审查分支的E提交由root正常保存；作者freeze中的pushed=false仅描述作者自身没有执行push。

| 检查 | 实际结果 |
| --- | --- |
| 官方布局核验 | v0.40.16三份源码准确Git blob/SHA256；相对v2入口、legacy移除及API child digest语义分别核对 |
| 修复前证据 | C2通用inventory对官方样式链接实际拒绝；新草稿19个方法中的同一方法3个subTest实际失败 |
| 修复后定向 | 36个方法，19新+17既有；52个实际subTest回调，1.426秒，全部通过 |
| 类型与静态 | mypy实际5个路径/5个source files、Ruff、格式、module-size、既有security scanner全部exit0 |
| 原边界保持 | native通用清单/发布器、原workflow与17项原合同测试均与C2字节一致 |
| 原件归档 | 作者23成员均能按UTF-8逐字节还原，长度/摘要与实际原件匹配；保留combined RED的采集限制 |

完整回归实际于`2026-11-14T16:37:49.936583Z`启动，`2026-11-14T16:42:30.915439Z`完成：102/102、exit0、source_drift=[]，stderr为空。stdout SHA256为`0d1bee4e82001511f12291d9c3be0867228a5a396f58b49d3acd176ef3eed61e`；独立timing原件记录280833毫秒。运行期间未移动本地HEAD或修改被冻结源码；这份准确源码已正常同步为审查分支E。

源码与合同冻结回执在`evidence/source-bindings.json`及`evidence/original.patch`。作者原始命令、环境、退出码和输出在`evidence/author-validation.json`，全量原件在`evidence/full-regression.json`。没有用日志字符数、耗时或合成测试计数填充真实模型usage。

本次是确定性工程验证。已完成托管尝试的真实symlink目标未被工件保留；补丁没有经过第二次原生任务验证，不证明OpenCode接受配置、Skill实际加载、完整session/usage或任何效果提升。完整原生任务、独立新任务与消费者真实门禁保持未完成。
