# Design: adk-v3-product-maturity

## 产品边界

ADK 3.0 分为五个明确层次：

1. `model`：版本化 manifest、profile、asset、target、workflow 数据模型。
2. `compiler`：解析 profile，生成 target-specific export plan 和确定性产物。
3. `installer`：plan、冲突检查、staging、backup、receipt、rollback。
4. `quality`：validate、security、benchmark、eval 和 release contract。
5. `adapter`：direct export 与 external handoff target 的显式适配器。

Shell 只负责稳定入口和环境定位，结构化逻辑进入 Python 包。实现保持 Python 3.8+ 兼容，以满足当前工作机；CI 使用受支持的较新 Python 验证，不使用 3.11 专属语法。

## CLI 契约

- `validate [--strict] [--summary-json]`
- `catalog build|find`
- `match --text ...`
- `export --target ... --profile ... --out ...`
- `install plan|apply|rollback`
- `benchmark run|report`
- `security check`
- `eval run|compare|report`
- `release check|build|publish`

未配置真实发布 backend 时，`release publish` 必须失败。Codex external handoff 只产生 handoff metadata，不进入 direct export bundle。

## 安装安全

计划文件记录 source/destination digest、目标 adapter、完整预期操作、冲突和版本。apply 会从 manifest 重新解析期望资产，只接受校验通过且未过期的计划；每次 apply 强制创建备份和 receipt。rollback 在写入前预检所有安装项与备份，重复安装时恢复上一 receipt。非 ADK 管理路径、plan 篡改、路径穿越、符号链接逃逸、digest 漂移和版本不匹配均拒绝执行。

## 评测

确定性层覆盖 schema、路由、导出、安装、发布和负向安全用例。真实运行时层通过 adapter 运行固定任务集，记录 task success、route accuracy、safety accuracy 和 latency；baseline/adk 共用审批策略与固定阈值。`eval compare` 要求 candidate 达标、指标不回退且至少有一项提升。缺少 runtime/auth 时只允许 `not-run`，不得伪造 pass。

## 回退

3.0.0 发布包保留 v2 manifest 迁移工具、命令映射和上一版本 tag。安装回退使用 receipt；代码回退使用独立原子提交，不修改参考子仓历史。
