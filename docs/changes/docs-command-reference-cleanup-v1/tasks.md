# Tasks

- [x] 识别 active README 中已退役命令引用。
- [x] 修正当前 README 的 maturity test 路径。
- [x] 扩展 `test_docs_cli_alignment.sh` 检查 active docs 的脚本/测试引用存在性。
- [x] 增加 retired token 回归，排除 historical `docs/changes/**`。
- [ ] 跑 fresh PR CI：2×contract、2×full regression、static-security、deterministic-eval-package。
- [ ] merge 后验证 main push CI。
- [ ] 由父仓执行 gitlink + `adk.lock` + current-status 原子 promotion，并验证 parent main CI。
