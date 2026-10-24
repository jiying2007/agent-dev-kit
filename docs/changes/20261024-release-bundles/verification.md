# F1 实现验证

实现者：`ai/root/adk_code_audit`。这份记录是实现验证，不是独立 Spec/Quality 审核。验证日期为 2026-10-24，工作分支 `fix/audit-boundaries-20261024`，父提交 `415590db44e88979185efb850e2339a3f95411ef`。

## 实现与合同

- 归档第一遍读取同时记录 `bundles/` 真实文件摘要、模式及目录条目，原有 compressed/decoded/member/name/JSON/metadata/PAX 上限和重复、冲突、链接检查不变。
- 先完成既有 release manifest、SBOM、source manifest、source count 和 source tree digest 校验，再把同一份不可变 `raw: bytes` 中的 source 复制到私有临时目录。两遍之间不重新打开归档路径；复制继续使用同一有界读取器，权限归一化为 0644/0755，临时根目录为 0700。
- 使用当前已加载的 `Manifest` 和现有 `_render_historical_selection` 从 source 数据重现每个 direct target。校验完整 target/count、文件路径集合、内容摘要、权限、export manifest 字节，以及存在的目录条目。归档目录标记允许省略；额外目录和目录模式漂移拒绝。
- `compiler.export_manifest` 仅把原内联清单构造抽为纯函数；正常 export 和 release verifier 共用原有 `adk-export-manifest/v2` 字段与序列化顺序，不新增 schema。
- 主 Agent 后续批准的输出预算已落实在现有 `targets.py` renderer：release 显式构造共享 `RenderBudget`，总输出、单文件、文件数和路径字节分别取自 `archive_io.MAX_DECODED_BYTES`、`MAX_MEMBER_BYTES`、`MAX_MEMBERS`、`MAX_NAME_BYTES`（默认 128 MiB、32 MiB、8192、4096）。同一状态跨全部 target 和 export manifest 使用，不在每个 target 重置。
- 有界路径把 `yaml.safe_dump` 接到分块 UTF-8 writer；在保留编码数据前检查剩余单文件/总预算，避免先建立完整放大后的 frontmatter 字符串。body 也通过同一 writer；support 文件先检查大小再分块读取；资产最少文件数提前校验，每个 support 和 export manifest 文件继续单独消费文件数。已有源文件大小、JSON 深度与成员数约束限制输入，输出超过预算时立即中止。普通 export/安装未传预算，继续走原有默认路径。
- 源包 Python 仅作为数据复制；不导入或执行。manifest/target schema 在使用前拒绝外部引用和嵌套引用作用域，避免归档 schema 发起网络解析。局部引用缺失/递归等外部库异常在 canonical verifier 边界变为结构化失败，同时保留原始异常 cause。
- archive-resource、strict-json、release-manifest 的旧“正例”缺 source 合同与 bundles，已迁移到共享测试夹具 `tests/release_archive_fixture.py`。夹具保留真实 schema、target contract 和 Agent/Skill，通过真实 `Manifest.validate(strict=True)` 与 `export_assets` 生成。未放宽 validator 或给非发布包添加豁免。

## 实际执行

所有命令的外层使用 `/workspace/scratch/712af632e2a5/audit-tools/rtk proxy`，环境为 `PATH=/workspace/scratch/712af632e2a5/audit-venv/bin:/usr/bin:/bin`、`PYTHONPATH=src:tests`。`python3` 为本轮独立 Python 3.12 解释器，PyYAML 6.0.3、jsonschema 4.26.0。

| 命令 | 实际结果 |
| --- | --- |
| 首轮四个 F1 行为用例，未修改生产实现 | exit 1；4 tests / 12.006s；9 failures；见 negative-results.md |
| 相同四个用例，核心实现完成后 | exit 0；4 tests / 19.251s；OK |
| `python3 -m unittest test_release_integrity test_archive_resource_bounds test_strict_json`，完成夹具迁移后 | exit 0；53 tests / 38.810s；OK |
| `bash tests/test_release_manifest_contract.sh`，加入历史/离线 schema/目录与 export manifest 验收后 | exit 0；archive bounds 22 tests / 0.890s；CI authority 4 tests / 0.028s；release integrity 20 tests / 34.313s；release rehearsal 1 test / 10.330s；全部 OK |
| `python3 -m unittest test_release_integrity.ReleaseInventoryTest`，补局部引用异常边界后 | exit 0；10 tests / 0.658s；OK；包括新的 CLI 结构化失败断言 |
| `python3 -m unittest test_install_upgrade.ExportOutputBoundaryTest test_install_upgrade.InstallUpgradeTest test_install_receipt_authority` | exit 0；20 tests / 6.824s；OK |
| `bash tests/test_module_size_budget.sh` | exit 0；status=pass；默认 30000 bytes；import fanout 26/28；support module count=0 |
| `git diff --check -- src/agent_dev_kit/compiler.py src/agent_dev_kit/distribution/archive_io.py src/agent_dev_kit/distribution/release_contract.py tests/test_release_integrity.py tests/test_archive_resource_bounds.py tests/test_strict_json.py tests/test_release_manifest_contract.sh` | exit 0；无输出 |

新增反例包括删除全部 bundles、删除 target、删除单文件、篡改 Skill、增加文件、文件模式漂移、虚假 target count、缺 export manifest、额外目录、目录模式漂移，以及改 Skill 后自行重算 export manifest。公开 publish 的无 bundle 变体在 GitHub CLI discovery 前失败；无实际发布。现有资源边界测试同时证实输入路径在首遍读取后被替换时，后续重渲染和 digest 仍使用原快照。

## 输出预算完成后的最终定向验证

此轮在主 Agent 完成候选版本 `8.0.40` 同步后执行；整包兼容探针仍固定历史基线 `415590db44e88979185efb850e2339a3f95411ef`。未修改 F2 smoke/process 函数。新增预算反例先红的结果见 negative-results.md。

| 命令 | 实际结果 |
| --- | --- |
| `python3 -m unittest test_release_integrity.ReleaseInventoryTest` | exit 0；16 tests / 1.498s；包括 UTF-8 精确字节、文件数、路径上限正例和减 1 反例，及 export manifest 自身超过单文件上限 |
| `bash tests/test_release_manifest_contract.sh` | exit 0；archive bounds 22 tests / 0.840s；CI authority 4 tests / 0.034s；release integrity 27 tests / 38.163s；release rehearsal 1 test / 10.013s；全部 OK |
| `bash tests/test_target_contracts.sh` | exit 0；target contracts PASS，含 9 smoke tests / 9.145s；无真实 Native runtime |
| `python3 -m unittest test_install_upgrade.ExportOutputBoundaryTest test_install_upgrade.InstallUpgradeTest test_install_receipt_authority` | exit 0；20 tests / 7.177s；OK |
| `python3 /tmp/adk_f1_compatibility.py` | exit 0；新有界 renderer 验收完整旧包 PASS，重建摘要仍为下述 680ab5…；历史时钟合同相同 |
| `ruff check src/agent_dev_kit/targets.py src/agent_dev_kit/compiler.py src/agent_dev_kit/distribution/archive_io.py src/agent_dev_kit/distribution/release_contract.py tests/test_release_integrity.py tests/release_archive_fixture.py tests/test_archive_resource_bounds.py tests/test_strict_json.py` | exit 0；All checks passed |
| `ruff check --select E4,E7,E9,F,B,UP,SIM,I src/agent_dev_kit/distribution` | exit 0；CI 该 scope 的严格选择全部通过 |
| `mypy src/agent_dev_kit/targets.py src/agent_dev_kit/compiler.py src/agent_dev_kit/distribution/archive_io.py src/agent_dev_kit/distribution/release_contract.py` | exit 0；Success: no issues found in 4 source files |
| `bash tests/test_module_size_budget.sh` | exit 0；status=pass；import fanout 26/28；无 oversize/support debt |

新预算矩阵使用真实小型 source：深层 JSON 转 YAML 缩进使单文件/总输出放大；两个 target 分别未超限但合计超限；80 个资产别名复用一个源文件；20 个资产重复输出同一 48 KiB support 文件；10 个资产各重复 100 个空 support 文件使 export manifest 超限。测试输入全部先通过原有归档预算，预期在生成阶段返回 `render_output_budget_exceeded`，而非等全部放大结果构造完再发现 digest 不匹配。没有进行内存耗尽实验。

## 精确基线的整包无漂移证据

仓外脚本 `/tmp/adk_f1_compatibility.py` 从本地 Git 创建独立 clean clone 并固定 `415590db44e88979185efb850e2339a3f95411ef`，使用当前实现重建完整 v8.0.39。实际命令：

```text
python3 /tmp/adk_f1_compatibility.py
```

退出码 `0`。产物为 `/workspace/scratch/712af632e2a5/f1-baseline-verify/agent-dev-kit-8.0.39.tar.gz`，完整归档 SHA256：

```text
680ab5bbf4340c5ae75e1e8441dc3531a50795d1c0d8e395a84448ba4429b487
```

与审查前精确基线构建及正式 v8.0.39 已核对摘要一致。新 canonical validator 返回 `status=pass`、`release_eligible=true`；把 target owner 的时钟推进到两个 source 均过期的 `2027-01-12` 后，历史包验收合同逐字段相同。独立测试还证实同一时刻的新 target 准入仍返回 `target_contract_stale`，历史验收不续期当前准入。

## 剩余 Gate 与边界

完整回归、独立只读审核、精确提交 CI 和发布由主 Agent 统一整合；实现者尚未提交、推送或发布。本轮没有执行真实 Native runtime、G22、LTA 或产品资格。当前正式 direct targets 是 static 合同；未来 runtime-certified 合同仍沿现有历史 renderer 的 Native trust owner 检查，其现场验收不由本记录授予。

归档与输出预算已同时落实；它们约束输入和已生成的数据规模，不能替代操作系统的 CPU/内存隔离。完整回归和独立 Spec/Quality 结论仍由主 Agent 收口，不能用这里的定向 PASS 替代。
