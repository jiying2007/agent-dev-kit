# 设计说明：adk-v3-1-rc2-target-conformance

## 架构

```text
manifest + source asset
        |
        v
 TargetContract registry ---- target check / target smoke
        |
        v
 TargetAdapter.resolve/render
        |                  |
        v                  v
 export manifest v2    install plan v2 -> receipt v3 -> rollback
```

- `targets.py` 是路径、frontmatter、权限、support file 和 target capability 的唯一实现。
- `compiler.py` 只负责原子输出目录与 export inventory，不再拥有 target-specific 分支。
- `installer.py` 以 renderer 的 file-level 结果生成/复核计划，禁止自行拼接 `agents_dir/skills_dir`。
- contract JSON 位于 `manifests/target-contracts/`，并由 Draft 2020-12 schema 校验。

## TargetContract v1

必填字段：`schema`、`target`、`status`、`source`、`supported_asset_kinds`、`layouts`、`frontmatter`、`permission_profiles`、`support_directories`。

| Target | Agent | Skill | 当前状态 |
|---|---|---|---|
| `claude-code` | `agents/<name>.md` | `skills/<name>/SKILL.md` | experimental |
| `opencode` | `agents/<name>.md`，含 `description`、`mode: subagent` | `skills/<name>/SKILL.md` | experimental |
| `hermes-agent` | unsupported | `skills/<name>/SKILL.md` | experimental |

通用 Skill frontmatter 至少包含 `name`、`description`；provenance 放在 `metadata.adk`。Agent permission profile 由 manifest 中每个 Agent 的显式 `permission_profile` 决定，不从提示词推断。

## 权限映射

- `read-only`：需求、架构、测试、安全、review、BSP；禁止写，shell 默认拒绝或仅允许只读工具。
- `code-write`：driver/component/application；允许编辑，shell 需要目标运行时默认/ask 策略。
- `build-release`：构建发布；编辑与 shell 均为 ask/default，不授予无条件外部发布。
- `diagnostic`：性能/硬件；禁止普通编辑，允许受控 shell 诊断。

contract 保存 target-native 表达；core 只验证 profile 名称和目标映射存在。

## 输入与输出契约

### export

- 输入：target、profiles、optional skills、可选 `asset_kind`、output directory。
- 输出：原生树及 `adk-export-manifest.json` schema v2；inventory 为逐文件 path/hash/mode/source asset。
- 错误：unknown target/kind/profile、unsupported kind、collision、symlink/unsafe support path 在任何 output replace 前失败。

### install

- 输入：与 export 相同的资产选择，target root，`mode=copy`，TTL。
- plan v2：逐文件 operation，绑定 manifest digest、contract digest、active receipt digest、rendered sha256、destination、UUID、带时区时间和最多 1440 分钟 expiry。
- receipt v3：逐文件 installed/backup hash、previous receipt hash 和 contract digest。
- `symlink`：3.1 明确 unsupported，CLI exit 2，不产生 plan。
- apply：重新 render 并逐项核对 plan，不信任 plan 中内容；目标锁内 staging/backup/replace。
- rollback：v3 逐文件回收；旧 v1/v2 receipt 继续走 legacy tree rollback。

### target check/smoke

- `target check --level static` 校验 contract、支持种类、路径、frontmatter 和全部 resolved assets，可输出 summary JSON。
- `target smoke` 先执行 static；没有显式 runtime command 时返回 `not-run` 并以 exit 2 表示认证未发生；runtime command 必须由调用者提供，结果保留 target、阶段、started time、duration、command/output digest 与 exit。
- exit 0=`pass`，2=`usage/unsupported/not-run`，1=`contract/runtime/internal failure`。

## Schema 与版本

- `manifest.schema.json` 保持 Draft 2020-12，顶层列出全部 26 个 SSOT key，`unevaluatedProperties: false`。
- `Manifest.load()` 使用固定依赖 `jsonschema==4.23.0` 执行 schema，再执行跨字段/文件系统语义校验。
- product 版本 `3.1.0-rc.2`，schema version `3.1.0`；release notes 明确这是 target conformance prerelease，不是 M5 认证。

## 迁移和回滚

1. 旧 export 目录必须重新导出到空目录或使用 `--clean`，不做隐式搬迁。
2. 旧 v1 install plan 重新运行 `install plan`；apply 会明确拒绝旧 schema。
3. 旧 v1/v2 receipt 只支持原结构 rollback；rollback 完成后再用 v2 plan 安装。
4. rc.2 失败时先用当次 receipt rollback，再从保留且 checksum 匹配的 rc.1 artifact 重装并核对 managed hashes；随后回退源码/gitlink，不复用 rc.2 plan。

## 验证策略

- contract schema、未知 target/unsupported kind、unsafe support file、permission profile 缺失负例。
- 每个 target/kind golden tree + frontmatter；export/install hash 一致。
- plan expiry/tamper/old schema/symlink/no-partial-output；v3 receipt rollback + legacy fixture rollback。
- manifest unknown key/schema violation、JSON/YAML mirror、Python 3.8 compatibility。
- CLI 非仓库 cwd smoke；ADK full；root quick/full；release check/build/rehearsal。

## 证据诚实性

static pass 仅表示文件和契约符合当前锁定规范。真实 discovery/load/trigger/permission 必须由目标 runtime smoke 产出，缺失时状态保持 `experimental`，成熟度保持当前级别。
