# Design: Native Target Conformance Receipt V1

## Receipt 与 contract 绑定

Target contract 的 runtime evidence 不再指向任意“证明文件”，而是指向 typed receipt。Evidence reference 与 receipt 同时携带 target、runtime version、bundle digest、contract digest；loader 重算文件 hash、normalized contract digest 和所有 identity。

Normalized contract digest 将 `adapter.conformance.evidence=[]`、`last_verified_at=null` 后 canonical JSON hash。这样 receipt 可以先绑定稳定 contract 内容，再把 receipt path/hash 与验证时间回填 contract，而不会形成 hash 自引用。

## Trust policy 边界

Typed receipt 与 canonical digest 只能防止误配和非一致修改，不能证明是谁生成了 receipt。Target adapter 因此新增 managed `conformance_trust_policy`：

- 当前三个 target：`enabled=false`、`trusted_authorities=[]`、`verification_backend=not-configured`。
- Runtime branch 只允许配置非空 authority 集及 `external-signature-verifier` 或 `ci-provenance-verifier`。
- Production `load_target_contract()` 当前不注入 verifier，所以任何 runtime promotion 都 fail closed。
- 私有 validator 的 verifier 参数仅用于 synthetic 结构单测，不是 production trust backend。

因此 CR5 没有声称解决密码学身份。外部签名、CI OIDC/provenance 验证器及其受管注入仍是明确 open item。

## 三阶段独立性

Receipt 固定按以下顺序记录三个对象：

1. `discovery`：证明 runtime 原生发现 skill metadata，不调用 skill。
2. `load`：独立命令显式加载 SKILL body canary。
3. `trigger`：另一条独立命令触发 skill 并读取 reference canary。

三个 stage 的 command digest 和 result digest 必须分别唯一。单一 prompt、同一输出、聚合 README 或重复 hash 不能代替多个 stage。

## Claude Code 2.1.138 最小权限方案

运行目录必须是 `mktemp -d`，仅把固定 ADK bundle 安装到临时 `.claude/skills`；不写用户配置、不安装 live target。三次命令共同使用：

```text
claude --setting-sources project --tools "" --permission-mode dontAsk \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --no-session-persistence --no-chrome --max-budget-usd 0.05 \
  --output-format json --json-schema '<stage schema>' -p '<stage prompt>'
```

- 总预算硬上限 USD 0.15，每 stage 不超过 USD 0.05。
- 禁用 tools、user/local settings、MCP、Chrome 和 session persistence；仅复用用户 OAuth 身份。
- discovery 只返回 `adk-requirements-triage` metadata description。
- load 显式调用该 skill，只返回 SKILL body heading canary `需求分类规则`。
- trigger 使用另一次显式调用，只返回 reference canary `Target Scope` / `Product / device`。
- 原始 stdout 只允许存在于临时进程内；校验 structured output 后仅记录 digest、exit/time 与脱敏字段，并删除临时目录。
- 任一配置、认证、权限、预算或 stage 失败即停止，不回填 runtime contract。

## 本轮执行结论

首次 discovery 在模型调用前被 CLI 拒绝，因为尝试的空 MCP 参数 `{}` 缺少 `mcpServers` record。主线随后授权合法 empty MCP record；一次受控执行未产生 structured output，最后一次按精确参数直接执行则明确返回 `Not logged in`，API duration、token 和 cost 都为零。依据停止条件，没有放宽 user/local settings 或认证边界，也没有执行 load/trigger 或生成 receipt。三个 target 因此保持 static/not-run，native field evidence 仍 open。

## 回滚

删除 receipt/trust policy schema 与 loader 分支，并把 target contracts 回退到 static schema 即可；当前没有 runtime-certified target 或 live 安装需要数据迁移。


## 7.3.0 后续：受管 verifier 注入

原设计中“production loader 无 verifier 时 fail closed”的安全边界保留，但“不存在 production 注入路径”这一软件缺口由 7.3.0 关闭。loader 仅在 runtime conformance 分支读取 owner-reviewed managed registry，并构造 digest-pinned Sigstore/cosign verifier；static target 不读取 verifier。

registry 默认无 authority。启用 authority、加入具体 receipt/bundle 绑定和切换 target runtime conformance 仍是独立变更。真实 discovery/load/trigger、认证和签名 receipt 未完成时，target 必须继续 static/not-certified。
