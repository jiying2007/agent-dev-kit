# F1 实现交接

- 当前角色：实现者 `ai/root/adk_code_audit`，不是独立审查者；需求/设计由主 Agent 冻结。
- 已完成：行为负例先红、source 重渲染验证、compiler 清单纯函数复用、真实最小夹具迁移、定向发布/安装/归档/JSON/模块预算验证、精确基线整包无字节漂移验证；后续批准的 renderer 总字节/单文件/文件数/路径预算也已先红后绿，含分块编码与 export manifest。独立复核发现的三个 P2（Native schema 外部解析、support root 先越界遍历、archive registry 授权宿主执行）也已按主 Agent 冻结边界先红后绿；生产 fix 和定向测试已冻结。
- 当前工件：`verification.md`、`negative-results.md` 与 `tasks.md`。
- 已排除：只信包内 export manifest 自有摘要；给 `release_eligible=false` 包豁免；导入或执行归档 Python；两遍读取之间重新打开归档路径；放宽历史合同以授予新的当前准入；信包内 schema 授予源外目录访问；信包内 registry/二进制摘要授予宿主执行；跳过 runtime 信任验证后 PASS。
- 当前状态：生产源码已冻结，独立只读 reviewer `ai/root/release_governance_audit` 已接手 F1；其 F2 实现不作为该审核的独立范围。
- 待整合：独立只读 Spec/Quality 审核、完整回归、精确提交 CI 和远端流程由主 Agent 收口。
- 不得推断：定向测试 PASS 不等于完整回归或 Native/现场资格；工作区包含其他 Agent 的独立变更，不能覆盖或回退。
