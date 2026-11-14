# 观测与限制

- 2026-11-14：按任务关键词检索 `knowledge/L2-domain/lessons.md`，该路径不存在；未假定历史经验。
- 本执行环境 CPython 3.12.14，PyYAML/jsonschema 可用。`rtk` 不在 PATH；不伪装 wrapper 或安装未知工具。
  必要验证使用现有 Python/Bash 入口，保持原门禁与短日志；原仓库指令未修改。
- 未调用 Codex/Work 模型或定时任务。真实宿主任务观测仍需核验可用来源；不能用合成fixture补足。
- 已检查本地可用命令：`/usr/bin/dot` 是 Graphviz，不能当作 Dot agent；没有 Claude/OpenCode/Ollama 模型入口。
  现有 `native-claude-conformance.yml` 仅检验发现/加载/触发，不是八类真实任务A/B；没有启动它或安装模型运行器。
  GitHub Actions 的 workflow_dispatch 列表仅有历史 release 作业，未找到对应任务观测。
- GitHub connector 拒绝 workflow-specific runs URL；改用允许的仓库 Actions runs 集合完成只读核查。
  公共 API 的本地网络请求超时，不作为“没有数据”的证据；可用连接器结果为核查来源。
- 独立审查重现：通用 compare-trials 不解释任务 input/workspace/exposure refs，
  不同初始工作区的合成数据可被评为 improved；本轮新增前置配对校验，不更改原统计器。
- 独立审查发现通用输出 writer 可覆盖已读观察包；改用已存在的安全输出校验和完整读集合，
  对同路径、别名与错误输入保留回归。失败原始记录不删除。
- 首轮完整回归在 `test_profile_context_footprint` 失败：incident-response 的 potential_full_source_bytes
  为47259，上限46612，超出647字节；入口体积36266仍小于37797。保持原 ratchet，要求精简相关引用后复验，
  不把 source bytes 称为真实 runtime Token 或成本收益。
  修复仅精简 `mcu-memory-footprint.md`：2208降为1523字节，profile降为46574（上限46612）；
  保留全部新增与原边界，profile 6/6、content 71/71定向复验通过。
  随后澄清“不无故全量重建”，最终文件1529字节、profile 46580字节；再次6/6通过。
