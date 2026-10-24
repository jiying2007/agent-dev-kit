# 任务

- [x] 从验收条件补确定性负例并确认旧实现失败。
- [x] 迁移 archive-resource、strict-json 与 release-manifest 的最小正例：旧正例只含 version 和 source manifest，却声明有 direct target 而没有 bundle，不再满足完整性交付合同；复用真实最小 source/renderer 生成合法正例，不按 release_eligible 豁免校验。
- [x] 在既有归档与发布合同 owner 中补完整性验证，保留公共合同。
- [x] 抽出 compiler 已有 export-manifest 纯构造函数供 export 与 release validator 共用；保留真实 build 逐字节输出和原 export/安装回归，避免第二份 manifest 定义。已检索 export、release、quality、target-source-probe 与测试调用点；精确基线重建整包 SHA256 与原始正式摘要一致，见 verification.md。
- [x] 按主 Agent 新授权，在既有 renderer 补跨 target 的总字节、单文件字节和文件数预算；使用 archive_io 现有上限，frontmatter 在编码过程中限额、support 文件分块读取，预算包含 export manifest；先跑真实小型输出放大反例，保留普通 export/安装输出和已冻结 smoke 行为。最终 27 release integrity tests、22 archive tests、4 CI authority tests、1 rehearsal、20 install/export tests、target contracts（含 9 smoke）及定向 lint/mypy 全部通过，见 verification.md。
- [x] 修复独立复核的三个 P2：覆盖 Native receipt 分支实际使用的第三份 source schema，在引用解析前做同一 offline guard；support root 在任何 exists/rglob 前按 asset root 检查 containment，保留原 symlink 拒绝；release 公共入口固定禁止 archive Native verifier，并在构造 managed verifier 前拒绝 runtime conformance。真实 public validator 回归先红再绿（4 tests / 4 failures → 4 tests / PASS），普通本地 managed Native 默认语义保持。调用点已检索：私有 historical renderer 仅由 release validator、installation inventory 与定向测试使用；安装恢复不传新限制，默认保持原行为。最终 58 项 release 脚本用例、40 项 Native/安装/strict JSON、target contracts、历史整包、lint/type/module budget 均通过，具体命令和 raw pointer 见 verification.md。
- [ ] 执行 release integrity、安装升级、模块预算和完整回归，保存原始退出码及输出。
- [ ] 独立只读复核新实现及篡改反例；由主 Agent 统一提交、CI、发布核验。

定向验证已完成并存于 `verification.md`；完整回归和独立审核由主 Agent 在多任务整合后统一执行，尚未把该 Gate 勾选为完成。

新增预算调用点检索：`render_asset` 被 renderer、target check 及 target-contract shell 测试调用；`_render_main` 有 intent-boundary shell 用例；`_render_historical_selection` 同时用于 installation inventory 与 release validator。新增可选参数默认不改变既有调用者，只由 release verifier 显式提供预算。F2 smoke/process 范围不修改。
