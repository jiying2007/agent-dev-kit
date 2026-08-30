# 验证证据：official-source-toolchain-refresh-20260830

## 已通过

| 命令 | Exit | 证据 |
|---|---:|---|
| `tests/test_official_docs_timezone.sh` | 0 | +08:00 治理日跨 Kiritimati/Adak 一致；future retrieved_at 负例失败 |
| `scripts/check-official-docs-governance.sh --summary-json` | 0 | 69 sources；evaluated_at=2026-08-30；failures=0 |
| `tests/test_python_launcher.sh` | 0 | auto 3.12 优先、显式 override、旧 Python strict fail-fast |
| `scripts/check-agent-ecosystem-standards.sh` | 0 | checks=545；sources=11；negative_fixtures=13 |
| `scripts/devkit.sh validate --strict` | 0 | strict 通过；宿主 Python 3.8 仍明确 development-only |
| `bash -n`（4 个修改 shell/test） | 0 | shell syntax 通过 |
| `git diff --check`（T3 范围） | 0 | 无 whitespace error |

## 支持工具链实测

`scripts/run-local-ci-parity.sh --python all --mode quick` 已在源码快照
`d079dd0660120cfcda4089ec23b7bd31faa566559c201105f124c704453d5c11`
真实完成固定 digest Docker 环境：

- Python 3.11.15：26/26、strict、static targets、routing 30/30、wheel、
  dependency audit 全部通过。
- Python 3.12.13：同一矩阵全部通过。
- source mount 为 read-only，work copy 为 isolated tmpfs，gate network 为 none，
  credentials 未挂载，release authority 为 none。

## 历史失败与最终复跑

| 命令 | Exit | 归因 |
|---|---:|---|
| 首轮 strict/parity | 1 | 并发中的 target-contract v2 暂缺 adapter；不包含 official source expiry |
| 主线 target 修复后 strict | 0 | 当前工作树通过 |
| 主线 target 修复后 Python 3.11/3.12 quick | 0/0 | 完整矩阵通过 |
| 宿主 `tests/run_all.sh` | 1，63/64 | 唯一失败为并行 profile 调整造成的 embedded-fullstack Skill 排序 drift；T3 相关测试全部通过 |

T3 completion claim 为 `pass`。宿主 Python 3.8 的 strict 输出仍只作 development
evidence；支持工具链结论来自上述隔离 3.11/3.12 parity。
