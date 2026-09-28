# 方法来源的规范仓库身份

## 目标

`external_agent_pattern_contracts.json` 的本地参考仓方法条目不能继续把历史别名当现行仓库。记录规范 URL、exact pin、只读远端观察和时间，同时保留旧 URL 的历史归因；不将远端更新自动提升为采纳或 runtime。

## 验收

1. OpenSpec、VibeFlow（两条方法）、planning-with-files、Scale Engine 五条记录具有一致、有限的当前来源身份；历史别名保留。
2. 现有离线 checker 拒绝缺 pin/HEAD、非法 SHA、矛盾的 same/different、未批准主机、未来日期和同一 local_path 冲突。
3. `retrieved_at` 仍表示旧方法阅读时间；`canonical_checked_at` 只表示当前远端元数据复核，不冒称重读方法或核验提交祖先关系。
4. 严格校验、Python 3.8 正负例和方法边界检查通过；不修改根仓 pin、脏参考 checkout 或 ADK runtime。
5. checker 对 manifest 输入设 2 MiB 上限，拒绝 symlink 与重复 JSON 字段；测试替换输入不能绕过同一门禁。
6. 独立 ADK 默认不依赖父仓；显式提供根仓 reference lock 时，离线核 URL 和 exact pin；显式提供观察期限时拒绝过期或未来观察。
