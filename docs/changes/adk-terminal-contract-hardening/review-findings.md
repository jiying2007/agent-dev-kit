# 独立审查发现：adk-terminal-contract-hardening

- Review Scope：root performance wrapper、manifest/schema、installer contract、Python/依赖/CI、doctor、release SBOM、quick/full runner 与迁移文档。
- Requirement Baseline：`proposal.md`、`design.md`；不放宽预算、不伪造 remote/runtime/field 证据。
- Verification Baseline：定向、strict、security、release、ShellCheck、quick、full 与根 full 已有命令证据。

| ID | Severity | File | Evidence | Required action | Status |
|---|---|---|---|---|---|
| TC-001 | major | `scripts/check-adk-performance-ops.sh` | 包装器只确认 timing mode，真实 quick 超预算仍可假绿。 | 调用 canonical strict budget checker，并保留超预算负例。 | fixed |
| TC-002 | major | `src/agent_dev_kit/model.py` | typed schema 扩展后每次 load/validate 重复解析和 meta-validation，`manifest_validate` p95=557.465ms。 | 按 schema 原始字节缓存已验证 validator，容量有限且内容变化自动失效；manifest 数据仍逐次校验。 | fixed |
| TC-003 | major | `tests/run_all.sh`、`tests/test_validate.sh` | 单次 quick 曾达 154962ms；首轮分层实现又因未定义 `MODE` 在 `set -u` 下退出。 | 显式传递 `quick/full` suite mode；quick 跑 quick validation，重型 product/taxonomy 保留 full，根包装器继续单独跑 product。 | fixed |
| TC-004 | major | `proposal.md`、`design.md`、`CHANGELOG.md`、`docs/usage.md` | nested schema 从弱 object 变为 typed/unknown-field rejection，但 breaking 段只说明 Python。 | 明示 schema breaking、strict migration、extension/rollback 边界。 | fixed |

## False Positives

- 根 full 的 current-status/evidence/subrepo/workspace 失败不是可通过弱化 policy 修复的代码回归：严格子仓含本轮未提交变更，旧 rc.2 digest 必然不再匹配。
- 本机 doctor fail 是新支持合同的正确结果，不应把 Python 3.8 源码偶然可执行改写为发布支持。

## Out-of-scope Suggestions

- 自动 commit/version bump/rehearsal、push、远程 CI 与运行资产 apply 需要 owner 授权和提交态，不由本 change 自动执行。
- 双 runtime、独立操作者、独立真实仓和 30 天 field evidence 继续由 Software M5 certifier 管理。

## Re-review Result

- blocker=0、major=0、minor=0、question=0。
- quick 16/16=65331ms，strict 120000ms gate pass；full 53/53 的最终复验在 `verify-report.md` 记录。
- typed schema cache 有内容变化失效回归；copy-only 与 nested schema 有独立负例；支持环境漂移由 doctor fail closed。
- Final Verdict：`pass`（仅本地 source/test change）；release/terminal 继续 blocked。

## Controlled CI continuation re-review

- Review Scope：`tools/local-ci/`、`scripts/run-local-ci-parity.sh`、隔离快照 security/file-mode fallback 与 CI waiver。
- Requirement Baseline：只有 `pip-audit` 可使用 bridge 网络；本地替代证据必须无宿主凭证、最小权限、身份可追溯且不能升级为发布/认证证据。
- Verification Baseline：同一源码快照上的 Python 3.11/3.12 full matrix 各 54/54 通过，但该结果不消除运行边界本身的缺陷。

| ID | Severity | File | Evidence | Required action | Status |
|---|---|---|---|---|---|
| TC-005 | major | `scripts/run-local-ci-parity.sh`、`tools/local-ci/entrypoint.sh` | 单个容器用 `--network bridge` 执行安装、测试、security、eval、release check 与 audit；实际权限大于“bridge only for dependency audit”的声明。 | 拆分离线 gates 与联网 audit phase；gates 强制 `--network none`，只有 audit phase 使用 bridge。 | fixed |
| TC-006 | major | `scripts/run-local-ci-parity.sh`、`tools/local-ci/Dockerfile` | Docker 未指定非 root UID；`cap-drop`/只读根文件系统虽降低风险，但未落实最小身份权限。 | 固定非 root user，并用真实 quick/full 验证 tmpfs、venv、wheel 与 audit 均可运行。 | fixed |
| TC-007 | major | `scripts/run-local-ci-parity.sh`、`tools/local-ci/Dockerfile` | runner 只按可变 local tag 选择工具镜像，不输出 image ID，也不核验 base/toolchain labels；旧或被替换的 tag 可被误当成本轮固定基线。 | 镜像写入可核验 labels；runner fail-closed 核验并输出 immutable image ID/contract identity。 | fixed |
| TC-008 | major | `src/agent_dev_kit/quality.py` | scanner 能报告 repository-escaping symlink，但后续 `path.is_file()`/`read_text()`仍会跟随该 symlink；stat 失败分支还可能静默跳过。 | symlink 只做边界判定、不跟随内容；inventory path 无法 `lstat` 时 fail closed，并增加回归。 | fixed |

### Re-review verdict

- blocker=0、major=4、minor=0、question=0。
- Final Verdict：`needs-fix`；不得把首轮 dual-version full 结果作为最终 CI waiver pass 证据。

### Post-fix re-review

- TC-005：gates/audit 已拆为两个容器，源码仅有一个 `--network none` gates 路径和一个 `--network bridge` audit 路径；双版本 full 实跑通过。
- TC-006：镜像内固定无登录 `adk-ci`，实测 `uid=65532(adk-ci) gid=65532(adk-ci)`；quick/full、venv、wheel 和 audit 均在该身份通过。
- TC-007：runner 核验 `contract=v2`、base digest、Python version 和当前 Dockerfile+entrypoint definition hash，并输出 immutable image ID；同名旧镜像会 fail closed。
- TC-008：所有 inventory 项先 `lstat`；symlink 记录边界后立即跳过内容读取，无法 inspect 时直接失败；外链 secret fixture 只报告越界、不报告被跟随内容。
- 复验证据：source snapshot `33ab17d4ef6b21e3bb7a7cce2a58bb04ae437a4789dba621bf3fd74970e1a2ac`；Python 3.11/3.12 各 54/54，独立 audit 均无已知漏洞。
- Final Verdict：`pass`（仅本地 CI waiver/source-test 范围）；blocker=0、major=0、minor=0、question=0。release/remote CI/runtime/field 仍不在本结论内。
