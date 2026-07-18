# 负结果记录：adk-terminal-contract-hardening

## 已验证的负结果

| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-18 | quick regression 通过即可证明性能预算通过 | 将真实 timing JSON 交给 strict budget checker | quick 150665ms 超过 120000ms；根包装器仍显示通过 | 必须接通 strict checker并优化执行，不接受只检查 mode |
| 2026-07-18 | manifest strict validate 足以证明安装合同一致 | 对比 manifest、installer 与 usage 文档 | manifest 默认 symlink，installer 拒绝 symlink，文档同时承诺两种模式 | 需要跨层合同测试和 typed schema |
| 2026-07-18 | 当前本地安全检查等于完整依赖审计 | 检查本机质量工具和 CI 合同 | 本机 Ruff、pip-audit、类型和覆盖率工具不可用；远程结果未核验 | 未执行的外部门禁不能记为通过 |
| 2026-07-18 | 按 Build 规则检索 `knowledge/L2-domain/lessons.md` | 对指定路径执行关键词检索 | 文件不存在，命令退出 2 | 保留负结果并使用现有 change/Hub 原始证据，不伪造历史经验 |
| 2026-07-18 | typed schema 扩展不会影响既有 benchmark | 运行 3 次 platform benchmark | manifest validation p95=557.465ms，超过 500ms | 不放宽预算；消除重复 schema parse/meta-validation并增加内容变化失效测试 |
| 2026-07-18 | 单次约 100 秒即可证明 quick 稳定满足预算 | final quick timing + strict checker | 154962ms，strict 正确退出 1；validate 单项 39059ms | quick 必须按反馈层分层，重型 product/taxonomy 保留在 full/根包装层 |
| 2026-07-18 | 首轮 suite mode 传递可直接工作 | 运行 quick fail-fast | `MODE` 未定义，`set -u` 立即退出 1 | 改用显式 `SUITE_MODE` 并在同一优化根因 retry budget 内复验 |
| 2026-07-18 | 根 full 可在未提交候选上全绿 | 执行 62 项根 full | 55/62；旧 release digest、strict dirty 和派生 evidence/status 失败 | 不篡改旧 rc.2 证据；提交/version/rehearsal 必须由 owner 后续授权 |
| 2026-07-18 | RC2 artifact 可从 release commit 精确重建 | 从 `dd67b48` commit archive 构建并与旧 SHA 比较 | 重建为 520 files，旧最终 artifact 为 521 files；差异是 Git 忽略的 `history.log` 被旧构建器收入 source distribution | RC3 构建器排除 `*.log` 并加归档负例；rehearsal 使用 checksum 有效的历史实际 RC2 artifact，同时保留该 provenance 缺口 |
| 2026-07-18 | 在 `--cap-drop ALL` 容器中用 `cp -a` 复制只读源码 | Python 3.11 local parity quick | `cp` 尝试保留 owner 并遍历 `.git`/build/cache，因无 `CAP_CHOWN` 和 Git object 读取边界失败 | 不恢复 capability；改用 tar stream、`--no-same-owner`，并排除 Git 和构建残留 |
| 2026-07-18 | 让容器直接从仓库 bind mount 创建 tar stream | Python 3.11 local parity quick retry | 工作区中 owner-only 文件对容器 user namespace 不可读 | 不批量修改用户文件权限；改由宿主当前用户生成排除残留的 `/tmp` 快照与 SHA256，再只读挂载给容器 |
| 2026-07-18 | 宿主快照的执行位会原样穿过容器 tar | Python 3.11 build、doctor 后进入 strict validate | 容器二次解包后个别 helper 不可执行 | 仅在容器 tmpfs 副本内规范化 `u=rwX,go=rX`；不修改宿主 mode、不增加 container capability |
| 2026-07-18 | Docker `--tmpfs /work:rw,nosuid,nodev` 默认允许执行 | 读取容器 mount flags | `/work` 实际包含 `noexec`，直接调用 shell helper 必然失败 | 对隔离 `/work` 显式增加 `exec`；继续保留 `nosuid,nodev`、只读根文件系统、cap-drop 和 no-new-privileges |
| 2026-07-18 | ADK standalone CI checkout 可运行 ecosystem contracts | Python 3.11 quick 17 项 | 16/17；external pattern checker 强制要求 `llm_agent` sibling reference clones | 增加默认可移植、显式 strict 的 local source policy；standalone 仍严格校验 URL/provenance/method-only，父工作区可用 `--require-local-sources` 强制本地镜像 |
| 2026-07-18 | security check 可在不挂载 `.git` 的快照运行 | Python 3.11 quick 17/17 后执行 security | scanner 仅支持 `git ls-files`，无法枚举快照文件 | 增加有界、确定性的 filesystem fallback，排除 Git/生成缓存、限制 50000 文件并在结果中声明 inventory source；Git 模式保持默认 |
| 2026-07-18 | full suite 可在不挂载 `.git` 的快照验证 file modes | Python 3.11 full | `test_file_modes` 无法读取 Git index | 宿主导出 NUL 分隔 mode inventory 与 SHA256，只读挂载给 checker；inventory 模式禁止 `--fix`、拒绝 path traversal，默认 Git 模式不变 |
| 2026-07-18 | pip-audit 可在容器 noexec `/tmp` 中工作 | security/eval/release check 通过后执行依赖审计 | pip-audit 无法在 `/tmp` 执行临时构建 | `/tmp` 保持 noexec；仅将 `TMPDIR` 指向隔离且 `nosuid,nodev` 的 `/work/tmp` |
| 2026-07-18 | 仅用 `--user 65532:65532` 即可兼容全部脚本 | hardened Python 3.11 quick | 16/17；`whoami` 因 UID 未登记到 `/etc/passwd` 失败，`test_scripts_smoke` 正确阻断 | 不回退 root；镜像创建固定、无登录的 `adk-ci` 用户，再以同一 UID 完成双版本 quick/full |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk agent-dev-kit/scripts/check-performance-budgets.sh --strict --timing-json <quick.json>` | 1 | 真实 quick 超出 120000ms 预算 | 根审计命令输出 | Workflow | T1 |
| `rtk rg -n 'default_mode|symlink|mode != copy' agent-dev-kit` | 0 | manifest、实现与文档语义漂移 | proposal.md | Contract | T2 |
| `rtk bash -lc 'command -v ruff; command -v pip-audit'` | 1 | 当前环境缺少外部质量工具 | proposal.md | Environment | T3 |
| `rtk rg -n '<terminal hardening keywords>' agent-dev-kit/knowledge/L2-domain/lessons.md` | 2 | 指定 lessons 文件不存在 | negative-results.md | Knowledge | T0 |
| `rtk agent-dev-kit/scripts/devkit.sh benchmark run --iterations 3 --summary-json` | 1 | manifest validation p95=557.465ms > 500ms | `review-findings.md` | Performance | TC-002 |
| `rtk agent-dev-kit/tests/run_all.sh --quick --timing-json /tmp/adk-quick-terminal-final.json` | 0 | 测试本身 18/18，但 timing=154962ms | `verification-evidence.md` | Workflow | TC-003 |
| `rtk agent-dev-kit/scripts/check-performance-budgets.sh --strict --timing-json /tmp/adk-quick-terminal-final.json` | 1 | strict gate 拒绝超预算 quick | `verification-evidence.md` | Performance | TC-003 |
| `rtk agent-dev-kit/tests/run_all.sh --quick --fail-fast` | 1 | 首轮 suite mode 变量错误 | `tests/run_all.sh` | Source Test | TC-003 retry-1 |
