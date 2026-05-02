# Usage

## 1) 预检查

```bash
cd global-dev-kit
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
```

## 2) 资产安装

```bash
# 自动识别工具并软链接安装
bash scripts/devkit.sh install --tool auto --mode symlink --profile embedded-fullstack

# 指定工具与目标目录，安装 core + 强化 profile
bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile core --extra-profile release-hardening

# 生产安装：备份 + 安装报告 + 版本锁定
bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --backup --install-report reports/gdk-install-report.md --lock-version 0.3.0

# 在 profile 基础上叠加可选技能
bash scripts/devkit.sh install --tool codex --profile core --with-optional-skill incident-rca-report
```

参数说明：

- `--tool`：`auto|codex|claude-code|hermes-agent|opencode`
- `--mode`：`symlink|copy`
- `--profile`：主 profile（默认 `embedded-fullstack`）
- `--extra-profile`：可选叠加 profile（可重复）
- `--with-optional-skill`：按需叠加可选技能（可重复）
- `--target`：覆盖 manifest 里的工具默认根目录
- `--backup`：安装前备份目标 `agents/skills`
- `--install-report`：生成安装报告
- `--lock-version`：要求 manifest version 匹配

## 3) 资产转换

```bash
# 导出到 Claude Code
bash scripts/devkit.sh convert --target claude-code --profile embedded-fullstack --out dist --clean

# 导出到 Hermes Agent（叠加发布强化）
bash scripts/devkit.sh convert --target hermes-agent --profile core --extra-profile release-hardening --out dist --clean

# 导出并包含可选技能
bash scripts/devkit.sh convert --target codex --profile core --with-optional-skill test-flakiness-triage --out dist --clean
```

## 4) 目录索引与触发匹配

```bash
# 生成 Agent/Skill/Profile 索引
bash scripts/devkit.sh catalog build

# 关键词检索
bash scripts/devkit.sh catalog find --type optional-skill --keyword 事故

# 触发匹配（0 命中，1 未命中）
bash scripts/devkit.sh match --skill requirements-triage --text "收到模糊需求或跨团队需求时"
```

## 5) 工作流命令

```bash
# 创建变更提案
bash scripts/devkit.sh propose --change can-fd-bringup --title "新增 CAN-FD bring-up"

# 标记已实施
bash scripts/devkit.sh apply --change can-fd-bringup

# 触发验证并生成 verify-report.md
bash scripts/devkit.sh verify --change can-fd-bringup

# 评审分级并生成 review-report.md
bash scripts/devkit.sh review --change can-fd-bringup --result pass --blockers 0 --majors 0 --minors 1

# 归档到 docs/changes/archive
bash scripts/devkit.sh archive --change can-fd-bringup
```

命令级 Evidence Index：

```bash
bash scripts/devkit.sh evidence append --file docs/changes/can-fd-bringup/negative-results.md --command "bash tests/run_all.sh" --exit-code 0 --summary "all tests passed" --evidence-path docs/changes/can-fd-bringup/verify-report.md --layer Workflow --artifact verify-report
```

注意事项：
- 必须按 `propose -> apply -> verify -> review -> archive` 顺序执行。
- `review` 只接受 `verified` 状态，`archive` 默认只接受 `review-passed` 状态。
- `proposal.md` 需补全单问题、充分性、边界、重复性与 breaking change 检查项。

## 6) 测试与回归

```bash
# 全量测试（validate + format + install + profile coherence + optional + convert + workflow + catalog + trigger matrix）
bash scripts/devkit.sh test

# 单项检查
bash scripts/check_format.sh
bash scripts/validate_assets.sh --strict
bash scripts/check_profile_coherence.sh
```
