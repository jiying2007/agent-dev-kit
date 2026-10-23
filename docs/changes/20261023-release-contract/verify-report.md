# 发布合同实施验证

实现者：`ai/root/implement_release`。冻结需求/设计由主 Agent 提供；本记录不代替独立 Spec/Quality 裁决或远端发布证据。

## 已落实行为

- 可发布构建按固定 tree 的 `ls-tree -z` 清单读取 `cat-file --batch` 原始 blob，拒绝不支持类型，保持模式，并核对 blob OID。Git replacement refs、export-ignore/export-subst、工作树 ignored/隐藏漂移不能改写选定来源。
- 验证、导出、源码打包均消费该快照 Manifest；显式 dirty/unbound 开发构建仍保留不可发布状态。
- 既有有界归档 reader 增量计算 source 文件摘要和数量；canonical verifier 核对 source manifest、版本、数量、摘要。全归档重复、异常成员类型、冲突和非法路径在读取期间拒绝。
- public publish 首先复用 canonical artifact 验证，上传已捕获的 tar、匹配 sha256 以及同格式的 release-contract 三份资产；dry-run 保持无输出写入。

## 验证结果

- 修复前新回归确实失败，见 `negative-results.md`。
- 完整 `test_release_manifest_contract.sh` 通过：22 项归档预算 + 4 项 CI 权威 + 13 项发布完整性 + 1 项真实跨版本发布 rehearsal。
- 14 项 strict JSON 回归通过。
- 隔离 `assume-unchanged` 与 `skip-worktree` 状态后的最终强化用例通过。
- ruff、distribution mypy、模块预算/架构合同、diff whitespace 检查通过。
- 原始日志与当前实现/测试逐文件 SHA-256 见 `evidence/`。

## 追加：集成 CI 的 focused 质量规则

集成检查发现先前默认 Ruff 命令未覆盖 CI 的 `E4,E7,E9,F,B,UP,SIM,I` 规则集。本阶段仅改动两份实现文件的三处代码：将 source reader 的闭包迭代改为显式有界读取循环，合并并排序 `archive_io` 导入，使用兼容 Python 3.8 的 `capture_output=True` 捕获 Git 子进程输出。未新增 suppress 或改变行为合同。

实际 focused Ruff 与 `distribution + release.py` 的 mypy（6 个文件）通过；22 项归档资源回归和 13 项发布完整性回归再次通过。本阶段日志见 `evidence/focused-quality-followup.log`，原红绿记录保留，实施 receipt 已追加阶段并更新当前源码 SHA-256。独立审核记录由审核者自行更新。

## 范围和剩余阶段

未更改发布 schema、CI、信任根或产品资格。没有真实远端发布、模型或设备运行。主 Agent 继续统一执行独立审核、最终版本集成回归、受保护合入和发布读回；这些阶段尚不在本实现记录中标为完成。
