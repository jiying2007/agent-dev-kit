# 现有路由导出 E0-E3 保守投入等级，调试审查证伪，A/B/A/B 性能证据纪律 — Tasks

- [x] TASK-001: 限定改造面并完成既有源码修改。验证：PR #198 diff 和 exact-head CI。
- [x] TASK-002: 正负边界、Profile/安全和 Python 3.8/3.11/3.12 全部回归。验证：ADK CI 38892568551 与 38893064699。
- [x] TASK-003: 固定实际发布身份与后续 Root 消费关系，不伪造模型/硬件有效性。验证：Release v8.0.20、Root Pin 证据。
- [x] TASK-004: 精确 head PR、main、不可变 Release 的软件链验证完成。验证：verify-report.md；Root 关系在下述注释说明。
- [ ] TASK-005: 真人独立 reviewer 复核提案/源码/证据并明确 owner decision 后调用 canonical review/ archive；不得通过 AI 自审自动勾选。

## Ownership 与并行冲突检查
- scope_write: 此文件夹为治理事实补录，不重新实现 PR #198 代码。
- scope_read: 既有 GitHub PR、CI、Release、Root pin；G21/G22 的独立资格状态。
- shared contract/routing/release 等权威无新增并行写入。
- 独立 reviewer 记录：GitHub PR #198 的 reviews 数量为 0，不能以源码合并替代。

## 轻量工件与收敛结论
- 实施来源：ADK #198。
- 软件层：已合并 + fresh-main CI + immutable Release。
- Root 消费：Root PR #227 merged main 58512342801e2d1336cc9f0e8b5fa48db4b4745d; fresh-main CI 38896819529 succeeded.
- 未闭环：外部真实证据及独立审查未签署；本变更包保持 active，不得伪造 review-passed。
