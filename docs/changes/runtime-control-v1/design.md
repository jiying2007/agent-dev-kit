# 设计说明：runtime-control-v1

## 架构影响
- D1：`runtime_control` package 提供唯一 `reduce_events` 与 `evaluate`。
- D2：Codex source adapter 只生成 canonical snapshot/events；所有 action 来自 Engine。
- D3：journal 只保存 control events；usage 从原 rollout snapshot 读取，不复制为第二 SSOT。

## 数据与配置影响
- D4：单一 state/event/decision v1，single manifest，single CLI；无兼容 reader/writer。
- D5：Goal journal 新建且为空；旧 goal/session coach cache 进入 backup 后从 active 路径删除。

## 兼容性与迁移方案
- D6：breaking major；不 dual-run、不 deprecate、不 alias；一次性原子 cutover。
- D7：仅整包 backup rollback；rollback 后不得读取新 journal。

## 验证策略
- D8：离线 fixtures 证明 old/new desired behavior，不在 runtime 保留 shadow path。
- D9：zero-residual scan + cross-repo bundle + source-to-live receipt 绑定最终 source/build/live。

## Domain Model
- Entity：ControlEvent、RuntimeState、Decision、Goal、UsageSnapshot、Progress、Checkpoint、Evidence。
- State：idle|active|completed|blocked|aborted；action：continue|checkpoint|compact|replan|stop|blocked|pass。
- Interface：Codex adapter -> Engine API -> renderer/gate。
- Boundary：thread updated_at 仅 liveness；progress revision 才表示信息增量。
