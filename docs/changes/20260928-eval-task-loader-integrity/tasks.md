# 本地任务

- [x] 核对 CLI 与 campaign 共用的 `load_tasks` 调用链及现有任务文件规模。
- [x] 为文件、limit、JSON 对象、唯一 ID 和有限资源增加校验；保留前 N 条评分语义。
- [x] 补 limit 后重复 ID/畸形记录、零 limit、超预算、重复 JSON 字段和 symlink 负例；Python 3.8 定向 `test_software_m5_ready.sh` 通过。
- [x] 直接评分入口拒绝空序列和重复 ID，Python 3.8 定向测试通过。
- [ ] 本批集中复验严格校验与相关门禁；完整 94 项回归及 clean commit 身份留待统一收口。
