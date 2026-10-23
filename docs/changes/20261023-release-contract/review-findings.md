# 独立审核：发布来源、归档完整性与发布资产

Reviewer：`ai/root/external_methods`。实现作者：`ai/root/implement_release`。

## 结论与范围

**Spec：pass。Quality：pass。未发现本次 release 修复范围内未关闭的 blocker 或 major。**

本审核覆盖 ADK-01、ADK-02、ADK-03 的非平凡代码 requirements/design/tasks，以及以下 8 个 release 实现/测试文件：

- `src/agent_dev_kit/release.py`
- `src/agent_dev_kit/distribution/release_artifacts.py`
- `src/agent_dev_kit/distribution/archive_io.py`
- `src/agent_dev_kit/distribution/release_contract.py`
- `tests/test_release_integrity.py`
- `tests/test_release_manifest_contract.sh`
- `tests/test_archive_resource_bounds.py`
- `tests/test_strict_json.py`

真实实现 target 为 `bf9ec8164e2c80394ce997f8a8b51515cad4746e` → `70094158251f3a11eaceee5d95cb63dfcea1e895`，head tree 为 `5bdab3551e6940e53ce5bdc9d3eedc4de678478d`。完整原始 Git patch 和逐文件 SHA-256 由同目录 `review-evidence.json` 绑定。完整 diff 还包含输出边界、使用说明及两份来源 freshness manifest 的工作，分别由 `ai/root/architecture_audit` 的独立输出边界、Harness 与来源刷新审核负责；本 review 的 Spec/Quality 结论限于上述 release 范围。

## Spec 审核

| 原问题 | 实现与独立核验 | 结论 |
| --- | --- | --- |
| ADK-01：工作树内容可进入声称绑定 clean Git 的 release | 身份捕获固定 commit/tree，`ls-tree -z` 和 `cat-file --batch` 读取对应 blob，禁用 replacement refs，核验 blob 内容摘要与模式；冻结 manifest 用于后续检查、编译和源码打包。除了作者的 ignored/隐藏 index/export attributes/blob replacement 用例，审核者增加 commit/tree replacement、隐藏 manifest 与 Skill 修改、worktree chmod 对照；产物与干净基线逐字节相同。 | pass |
| ADK-03：声明的 source digest/count 缺乏实际成员验证 | canonical verifier 通过既有 bounded reader 汇总全部普通 source 文件，复算路径与内容摘要，检查 count、嵌入 manifest 和 top-level manifest；拒绝重复、冲突、特殊类型及不安全路径。审核者增加嵌套排序、9 MiB 源文件、逐字节漂移、两种成员顺序的祖先冲突、重复目录、PAX override、带 payload 的目录及超限声明。 | pass |
| ADK-02：公共 publish 与 canonical contract 脱节 | version/文件名、checksum、canonical contract 和 eligibility 在发布前检查；tar、checksum、contract 三资产来自同一个已捕获快照。审核者把上传的 contract 与真实 verifier CLI stdout 作逐字节比较，并在捕获后同时替换三个本地输入；上传仍为已核验字节，临时资产随后清理。 | pass |

2026-10-23 交叉核对原始 audit 时，修正了上述两行曾互换的 ADK-02/03 编号。该编号勘误未改变两项实际审核内容及原 56 项测试证据；最终 target 后续因下述 focused 质量修复更新，完整 patch 已重新绑定。

明确保留 dirty/unbound 开发构建的非发布资格。dry-run 只返回计划，不创建或覆盖 contract，不执行发布进程；存在本地旧 contract 时也保持原内容。

## Quality 审核

实现复用已有 source surface、Manifest、bounded archive reader、canonical verifier 与 publication owner，没有引入第二套发布判定器。源码内容按块读入摘要，9 MiB 的非 JSON 源文件未作为完整 payload 留存；现有 compressed/decoded/member/name/metadata/PAX/header budgets 保持生效。成员顺序变化与正常控制通过，恶意成员在 extraction 前拒绝。

第一阶段独立实际执行共 **56 个测试方法**，其受测源码对应 `c06fd629fa9a08f3079e7a606f45e65fcccbfc28`：作者的 release integrity 13 项，审核者新设计的 probes 7 项，archive resource bounds 22 项，strict JSON 14 项，全部通过。原始执行计数、时长、命令、源码摘要和额外 probe 脚本见 `evidence/independent-review-execution.json` 与 `evidence/independent-review-probes.py`。测试数不代表真实 Agent 效果样本，测试耗时不作为性能收益。


## 追加复核：最终 focused 质量修复

最终提交在 `c06fd629fa9a08f3079e7a606f45e65fcccbfc28` 之后仅对本审核范围中的两个实现文件改了三处。审核者实际比较 Git diff、逐行阅读周边逻辑，并核对当前八个实现/测试文件与 `70094158251f3a11eaceee5d95cb63dfcea1e895` 的 blob 完全相同。六个文件保留第一阶段受测字节；`archive_io.py` 与 `release_artifacts.py` 的新旧摘要分别记录，不把原 56 项执行冒充最终源码的整套重跑。

| 变化 | 独立复核结果 |
| --- | --- |
| `archive_io.py`：循环内 lambda 改为显式 `while` 读取 | 每次仍按同一 `_CHUNK_BYTES` 读取同一个 tar 文件对象，空字节终止；长度、SHA-256 累计、截断校验和 `finally` 中 reader 状态恢复保持原逻辑。 |
| `release_artifacts.py`：合并及排序导入 | 原有六个导入名与来源模块不变，没有新增依赖或分支。 |
| `release_artifacts.py`：`capture_output=True` | 与原来的 stdout/stderr 分别设为 PIPE 对应；不启用文本转换，保留原 bytes 清单解析、失败检查与 60 秒 timeout。 |

本阶段审核者实际重跑 `InventoryReview` **3 项（0.584 秒）**和 archive resource bounds **22 项（0.156 秒）**，全部通过。其中独立 probe 再次验证 9 MiB 源文件增量摘要、成员排序、源内容漂移、PAX/祖先冲突及超限 header 的拒绝。完整原 56 项未再次运行。

另已阅读实现作者的 `focused-quality-followup.log` 与更新后的 `implementation-verification.json`：focused Ruff、mypy（6 个文件）、archive 22 项与 release integrity 13 项均记录为通过。这些结果明确归属作者；审核者未声称独立执行该轮 Ruff、mypy 或 release 13 项。新阶段原始输出和新旧摘要见 `evidence/independent-review-followup.json`。

## 限制与后续 delivery gate

- 本审核没有运行真实 GitHub 发布、签名/attestation 验证、付费模型、runtime 安装或产品现场试验。mock 上传验证的是本地调用及三个资产的字节关系。
- source inventory 证明归档内部一致性；clean Git 来源、构建主体和远端 tag/asset 的最终身份仍需对应 provenance 与真实发布读回。
- 同环境的重复构建通过；跨操作系统、Python/Git/gzip 版本的逐字节复现未实测。
- 完整集成测试、精确提交 CI、最终组件发布和 Root pin promotion 由整合者保留实际结果；这份 source review 不替代这些 gate。
- 本轮没有修改 workflow asset，因此未补造 workflow propose/apply/history，也未提升 G22、LTA、Native 或 Product M5 资格。
