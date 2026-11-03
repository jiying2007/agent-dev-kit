# 8.2.0 提交前检查

用户于2026-11-03明确要求检查，没问题就提交、推送合并、应用。范围为Goal合同能力及其受管接线；不混入其他Codex本地草稿。

## 结果与负例

- 独立上下文 `ai/root/review_goal` 首轮发现三项major：选中open项绕过依赖、JSON和文件读取边界不严格、当前状态work_in_progress扩展不兼容。
- 最小修复后，独立whole-diff复审Spec/Quality均PASS，44项Goal/state/strict JSON测试通过，未扩张原生Goal、预算或完成权限。
- 完整本机回归101组，98通过、3失败：Manifest taxonomy排序键冲突、技能目录投影未生成、旧Harness来源审查不再匹配。分别修复排序键、用canonical catalog generator生成目录、绑定真实独立七维源码审查记录。
- 三项失败入口分别重跑通过：test_manifest_consumer_boundary.sh、test_catalog.sh、test_harness_readiness.sh。该结果不冒充一次全绿的冻结快照全量回归，受保护PR/Main CI仍必须在exact提交上执行。
- validate --strict、release check、check-format、git diff --check通过。Python3.8为本机兼容环境，3.11/3.12由CI分别验证。

## 配置与兼容

- 新平台中立技能归ADK core；default等下游runtime profile由消费者注册，二者不混用。
- stage_order=15位于planning轻量计划之后、任务拆解之前，不复用其他资产排序键。
- 当前状态新增可选work_in_progress；两入口共用值校验。合同schema为adk.goal-plan/v1，无旧Codex schema fallback。
- profile footprint按新增技能正文及示例的实际字节增量更新，原负例仍需验证增长失败。

## 发布与回滚

- 版本同步至8.2.0；只有受保护main exact CI与canonical自动签名发布成功后才能进入Codex正式source importer。
- 回滚以之前8.1.5提交/不可变制品为源码锚点，消费者依据具体apply plan恢复备份。不移动旧tag，不清理本地dirty或历史Goal累计。
- 代码及合同测试不授予模型效果、真实token收益、设备/HIL、产品或owner放行资格。
