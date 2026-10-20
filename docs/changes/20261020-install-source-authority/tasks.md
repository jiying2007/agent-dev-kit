# Tasks

- [x] TASK-001：实现显式旧来源和历史库存验证，保留 receipt/path/mode 权威。Verify：installer 7 个新验收与既有 contract/receipt 41+8+5 用例通过；命令见 verification-evidence.md；关联 AC1–AC3。
- [x] TASK-002：修正 release rehearsal 来源参数并核验完整恢复。Verify：真实 artifact/CLI 正向及反向版本负测通过，已接入 release 回归脚本；关联 AC4。
- [x] TASK-003：更新 API/CLI 迁移、Python 3.8+ 文档和用例入口。Verify：test_install.sh、88 份当前文档的 docs/CLI alignment 通过；关联 AC5。
- [x] TASK-004：完成本地独立复核与完整回归。Verify：98/98 full、strict validate、release check、target/native/module 定向通过；独立源码审查无阻塞问题；CI 既有 focused strict mypy 扩展后 27 个文件本地通过。见 verification-evidence.md。
- [ ] TASK-005：主任务创建受保护 PR，以最终 commit 的真实 CI 验证 Python 3.8/3.11/3.12 和已有发布门禁，完成提交与合并闭环。Verify：记录实际远端 run/commit 证据；本地通过不代替远端结果。
