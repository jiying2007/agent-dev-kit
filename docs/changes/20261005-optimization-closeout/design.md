# 分阶段设计与恢复

- Phase A：修复回归 fixture 对当前 dirty 源码的耦合；隔离快照中测试 clean/dirty 两条路径，不把 fixture 身份当成产品证据。
- Phase B：先冻结严格解析接口，再迁移关键文件读取与负例；根仓和 ADK 各自拥有 typed 工具，跨仓不复制历史兼容入口。
- Phase C：将安全演练接入已有契约，统一只读结果与 fail-closed 语义；不引入后台 executor。
- Phase D：热点拆分与文档收敛；每次仅修改一仓，共享入口串行。
- Phase E：评测预注册、干运行及授权后的真实采集；质量、成功率、成本和可靠性分别报告。
- Phase F：冻结 final snapshot，串行/隔离回归与受支持 Python 矩阵、fresh review、归档和 final gate。

retry_budget：同类无信息增量失败最多两次，之后 replan。
staleness_threshold：源码修改后旧快照回执失效；禁止在运行中的 runner 上修改。
stop_condition：pass / replan / split / blocked；未闭环外部资格单独交接。
resources：源码写入串行；临时 fixture、矩阵 tmpfs 和输出路径独立；正式仓 Git refs/index、runtime HOME、Provider registry 不与测试并发写入。
rollback：保留当前分支和既有 dirty，不自动提交；隔离生成物有清单，代码按本 change patch 回退。
verifier：确定性测试与最终独立 review；最终结论不得仅复述执行者声明。
