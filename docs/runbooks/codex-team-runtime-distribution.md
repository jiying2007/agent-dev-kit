# Codex Team Runtime Distribution

## Goal

从私有 `agent-dev-kit` 源仓向团队 Codex 用户交付可审查 Skill，同时不发布 ADK Python 实现、测试和内部 change evidence。

## Repositories

- 私有生产源：`agent-dev-kit`。
- 团队发行仓：`ssh://git@192.168.1.4:10022/embedded/aicode/team-codex-assets.git`。
- 成员运行态：`~/.codex`，不进入 Git。

## Publisher flow

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash ./tests/run_all.sh --fail-fast
rtk bash scripts/devkit.sh release runtime-build \
  --profile team-core \
  --out dist \
  --summary-json
```

在团队发行仓中执行：

```bash
rtk bash ./scripts/team-assets.sh bundle plan \
  --artifact /reviewed/adk-runtime-team-core-<version>.tar.gz \
  --output .cache/bundle-import-plan.json
rtk bash ./scripts/team-assets.sh bundle apply --plan .cache/bundle-import-plan.json
rtk bash ./scripts/team-assets.sh build
rtk bash ./scripts/team-assets.sh doctor --scope all
rtk bash ./tests/run_all.sh
```

只有 owner review、两仓验证和 diff 审查通过后，才允许另行授权 commit/push。私有 ADK CI 可以自动生成候选 Bundle，但外部 Git 写入保持独立审批。

## Member flow

```bash
rtk git clone ssh://git@192.168.1.4:10022/embedded/aicode/team-codex-assets.git ~/codex
cd ~/codex
rtk bash ./scripts/team-assets.sh setup
```

`setup` 内部完成 build、plan、apply 和最终检查，用于首次安装以及团队仓拉取新版本后的同步安装；无变化时返回 `unchanged`。安装后新开 Codex session，确认 Skill discovery 与自然语言触发。成员只需团队仓只读权限；不需要访问私有 ADK 源仓，也不需要操作 receipt 或 rollback。

## Security and confidentiality

- Bundle 外层 checksum、内部逐文件 checksum、profile/asset manifest 和 tree digest 必须全部一致。
- Bundle 只允许 `bundle-manifest.json`、`checksums.sha256`、`LICENSE`、`sbom.spdx.json` 与 manifest 声明的 Skill support tree。
- 拒绝路径穿越、重复成员、symlink/hardlink、special file、敏感文件名和额外 source tree。
- Skill 本身是 Codex 可读提示资产，不能对成员隐藏；保密执行逻辑应留在受控 API/MCP 服务端。
- MCP/API transport、凭证、deny-path 和数据保留不由本分发链隐式启用，必须另走 owner review。

## Rollback

1. 团队仓导入失败：使用 `.cache/bundle-receipts/<id>.json` 执行 `bundle rollback`。
2. 成员安装失败：由维护者诊断；底层 receipt/rollback 作为维护能力保留，不作为成员日常操作。
3. 发行回退：恢复上一版团队仓 commit/release，成员重新执行 `setup`。
4. target drift 时 rollback fail closed；先审查成员本地修改，再决定保留或显式覆盖。
