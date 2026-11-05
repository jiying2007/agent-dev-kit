# ADK Python 3.12 单版本迁移与 GitHub Ruleset 保护（11.0.0 起）

本仓 Python 只负责构建、管理、测试与发布。11.0.0 只支持 CPython 3.12.x (`>=3.12,<3.13`)，这是去除 Python 3.11 的 breaking change，不改变纯 Skill 消费端运行时依赖。

## 本地独立 .venv

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[quality]'
python -c 'import sys; assert sys.version_info[:2] == (3, 12)'
bash scripts/devkit.sh validate --strict
bash tests/run_all.sh
```

旧 3.11 venv 不可原地转换或复用，必须用真正的 3.12 解释器重新创建。GitHub Actions 每个 Job 使用 pinned `actions/setup-python` 选择 3.12，不必再套一个短时 venv；本地隔离使用 `.venv` 或已有的受审查 Docker parity。

## 一次性迁移主分支 Required Check Ruleset

迁移前现有主规则集可能仍要求 `contract-py3.11` 和 `regression-py3.11`。**先验证新 PR 确实产生 `contract-py3.12`、`regression-py3.12`、`deterministic-eval-package` 等检查，再调整规则集。** 禁止沿用旧名字生成假绿，也不能停用 PR、strict/up-to-date、security、squash-only 或其它保护。

GitHub Ruleset 修改需要 repository Administration write 令牌；本仓普通 GitHub 插件没有对应写入能力。由可信管理员在干净的、与 GitHub main 精确一致的源工作树运行原有治理工具。当前 main 上的治理脚本支持显式 `--required-check`，因此不用先合并 breaking PR。

```bash
git switch main && git pull --ff-only
test -z "$(git status --porcelain)"
# ADK_GITHUB_ADMIN_TOKEN 必须由受信任的本地安全渠道提供，不得打印或写入仓库
python3.12 tools/control_plane/github_governance_admin.py \
  --repo jiying2007/agent-dev-kit --branch main \
  --required-check contract-py3.12 \
  --required-check regression-py3.12 \
  --required-check deterministic-eval-package \
  --required-check static-security \
  --required-check codeql-python \
  --required-check dependency-review \
  --required-check branch-gc-dry-run \
  --required-check platform-vnext
```

首先核查 dry-run 只有受审查的预期差异；在相同命令末尾加 `--apply`，它将验证干净 main/远端精确 SHA、写入 Ruleset 并重新读取检查。Ruleset 应保留八个真实必需检查以及 PR-only、strict required statuses、no unconditional bypass、no force-push/deletion、squash-only 与单维护者零强制人工 Review。

之后从远端读取实际 Ruleset，核验要求不再包含 3.11 并准确包含八个 3.12 / 安全 / 发布检查。**若未完成可信管理员写入，则保留 PR 未合并**；不要从 GitHub API 页面“branch protection enabled=false”推断不受保护，Ruleset 才是主线权威。

## 合并、发布及 Root 迁移顺序

新 required-check 配置确认后才可合并 11.0.0。用精确 PR HEAD 成功检查和新的 fresh-main CI 产生真实 Promotion Evidence，验证 Sigstore、不可变 Release、精确版本及归档摘要。

历史签名回执中 `python: ["3.11", "3.12"]` 仍是原版本事实，不重写也不替代新版本。11.0.0 凭据只允许 `python: ["3.12"]`。Root 必须在正式 Release 后通过一个受保护 PR **原子更新** ADK gitlink、版本/interface locks、Promotion Evidence/attestation、`tools/control_plane/adk_promotion_evidence.py` 的 `REQUIRED_PYTHON` 及相应反例测试；不得单独提前改 Root 验证器造成旧版本证据失败。

## 回滚与证据

如迁移失败，恢复 Ruleset 原 required contexts、旧 ADK 10.0.5 精确来源和其签名制品，并分别重建管理环境。不能将 CI 绿灯解释为当前 Product M5、G21 Native、G22 效果或 LTA-04 现场资格完成。不得使用 Codex/Work 付费模型回合来替代确定性测试。
