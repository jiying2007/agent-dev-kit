# 本地 CI Parity Runbook

本入口用于远端 CI 暂时不可用或被 owner 明确豁免时，在本机 Docker 中复现声明的 Python 3.11/3.12 验证矩阵。它是继续开发的替代证据，不是远端 CI 状态、release provenance、Software M5 certification 或 field evidence。

## 权限与 transport 边界

- transport：本机 Docker daemon。
- source：宿主当前用户先生成排除 `.git`/build/cache 的 `/tmp` 快照与 SHA256，并单独导出 NUL 分隔的 Git index mode inventory 与 SHA256；两者只读挂载，容器不读取 `.git`。快照再复制到容器 tmpfs；`/work` 仅为运行 shell helper 和 pip-audit 临时构建显式允许 exec，仍保持 `nosuid,nodev`；容器 `/tmp` 保持 noexec，容器不能写回宿主源码。
- network：验证拆成两个容器 phase；gates phase 强制 `--network none`，只有 dependency audit phase 使用 Docker bridge。`--prepare` 构建本地工具镜像时也需要软件源网络；两者都不传递宿主代理凭证、SSH、GitHub token 或环境 secret。
- identity：每个工具镜像必须带 contract/base/python/definition labels；runner 按当前 Dockerfile+entrypoint 内容核验 label，输出 immutable image ID，不接受同名旧镜像或被替换的 tag。
- tools：Docker、Python 3.11/3.12 pinned base image、ripgrep、ShellCheck、Ruff、pip-audit。
- deny-path：不挂载宿主 `HOME`、SSH、Git credential、Docker socket、`~/codex` 或 `~/.codex`。
- external writes：`--prepare` 只写本机 Docker image store；验证容器为临时容器。
- fallback：Docker 或网络不可用时，保持 `not-verified`，不得把宿主旧 Python 的结果升级为支持矩阵通过。

## 使用

先检查执行计划，不访问 Docker：

```bash
rtk scripts/run-local-ci-parity.sh --python all --mode full --dry-run
```

首次构建固定基线镜像并运行完整矩阵：

```bash
rtk scripts/run-local-ci-parity.sh --prepare --python all --mode full
```

后续复用本机镜像运行 quick 或 full：

```bash
rtk scripts/run-local-ci-parity.sh --python all --mode quick
rtk scripts/run-local-ci-parity.sh --python all --mode full
```

## 通过含义

通过只证明：当前工作树副本在记录的 Docker base/tool image 上完成 doctor、strict validate、format、ShellCheck、Ruff、target contract、回归、性能预算、security、deterministic eval、release check、pip-audit 和 wheel build。gates phase 在非 root、无网络容器中运行；只有独立 dependency audit phase 使用 bridge。快照不挂载 `.git`，security check 会明确报告 `inventory_source=bounded-filesystem-fallback`，在 50000 文件上限内扫描快照中的全部非生成文件；Git checkout 仍使用 `git ls-files` inventory。

standalone 快照不包含 `llm_agent` 父工作区的参考子仓。`check-external-agent-patterns.sh` 默认使用 URL/日期/decision/notes provenance 并把 sibling clone 视为可选；只有父工作区明确执行 `--require-local-sources` 时才强制这些路径存在。缺少 clone 不会启用外部代码或降低 method-only 边界。

以下状态不会被本入口清除：

- GitHub workflow 未运行或未取得远端 run URL/attestation；
- 工作树未提交、release rehearsal digest 漂移；
- tag、publish、provenance、Software M5 certification；
- 独立仓、第二操作者、真实 runtime 和长期 field evidence。

每轮输出 `source_snapshot_sha256`、`file_mode_inventory_sha256`、`local_ci_definition_sha256` 与每个 Python 版本的 `tool_image_id`。任何源文件、Git index mode、Dockerfile/entrypoint 或工具镜像身份在取证后变化都会使该轮本地 parity 证据失效，必须重跑或重新 `--prepare`。
