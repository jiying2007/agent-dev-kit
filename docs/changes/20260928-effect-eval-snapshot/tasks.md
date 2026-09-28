# 本地任务

- [x] 确认当前 `sha256_file` 与后续解析是两次路径读取。
- [x] 用同一有限字节执行摘要校验和输入/标签解析，拒绝 symlink 与超预算；报告显式 `snapshot_atomic=false`。
- [x] 临时副本在读取后变化、超预算、符号链接负例和现有 24 例通过；Python 3.8 定向 `test_effect_eval.sh` 与 Software M5 测试通过。
- [x] 当前 Python 3.8 quick 回归 52 项中 51 项通过；唯一失败 `test_runtime_bundle` 需要 clean commit，内部 3 项功能测试通过。严格校验、release check、格式与模块体积门禁通过。
- [ ] 当前快照 full 回归和独立复审留待统一收口；保持本地未提交。
