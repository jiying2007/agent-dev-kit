# 设计说明：aggregate-gate-evidence-reuse-v1

## 架构影响
- D1：根仓新增 `scripts/lib/same-run-evidence.sh`，封装 workspace fingerprint、
  evidence init/record/validate；数据只存在于 `check-all` 的 `mktemp` 目录。
- D2：`check-all.sh` 是唯一 producer/control plane。它在 full 开始记录初始
  fingerprint，为已执行检查写不可执行 JSON metadata，并只向随后启动的
  workspace aggregate 注入临时 evidence 环境。
- D3：`check-workspace-entrypoints.sh` 是 consumer。它只对 requirements 中
  的 allowlist 尝试复用；每次复用前重新计算 fingerprint，验证失败即调用
  原 `run_check`。internal evidence variables 进入 consumer 后立即取消 export，
  不继续传给 workspace 内启动的 leaf commands。
- D4：root regression 子测试不单独伪造 producer 结果；consumer 必须从
  整体 PASS evidence 中找到精确 `[PASS] test_name` marker。
- D5：check-all 预建 600 权限的 reuse report；consumer 只有在 evidence
  验证和 report append 都成功后才跳过原命令。父进程从 report 写入 result
  JSON 和人类摘要；stdout 的 `[REUSE]` 只用于诊断，不作为机器事实。

## 数据与配置影响
- context schema：schema version、suite、producer PID、real workspace root、
  workspace fingerprint、创建时间。
- check schema：context 字段、check name/path、script SHA-256、exit/status、
  output path/output SHA-256。
- reuse report：只允许 evidence 同级、owner-owned、非 symlink、非
  group/world-writable regular file；consumer/producer 名称受字符 allowlist。
- `check-all --result-json` 保留 schema v1 和既有字段，新增
  `same_run_reuse` 对象；旧 reader 可忽略。
- 临时目录权限为 owner-only；validator 拒绝 symlink、非 regular metadata/
  output、root/parent/digest/fingerprint 不一致。

## 兼容性与迁移方案
- standalone workspace、quick、smoke 不注入 evidence，因此保持完整执行。
- full 中 evidence 不可用时只降低性能，不改变 gate 结果。
- 不持久化迁移数据；退出时沿用 `check-all` cleanup 删除 evidence。
- 若新鲜 full 没有实际复用或 component timing 未改善，回滚 D1-D5，不修改
  任何 leaf check。

## 验证策略
- 单元：evidence 合法/失败/PID/root/output/script/fingerprint/symlink。
- 集成：fixture `check-all` 证明只给同父 workspace 提供证据、失败 producer
  不可复用、结果 JSON 可观测。
- 回归：`test_check_all_contract.sh`、新增 evidence contract test、
  `tests/run_all.sh`。
- ADK：change apply/verify、定向 change governance、必要的 full suite。
- 根门禁：quick、workspace standalone、新鲜 full result JSON。
- 性能：对比 906/207 秒基线；检查实际复用列表和 workspace component。

## 安全边界与 deny-path
- 本机制防止意外的历史、过期、失败、篡改和并发漂移证据；不对拥有本地
  仓库写权限且可控制父进程的恶意主体提供安全隔离，因为该主体本就能修改
  gate 源码。
- 不读取网络、凭证、`~/.codex` 私有状态，不写 repo 外持久目录。
- 无效 evidence 不输出敏感内容，只在 consumer 内回退执行。

## 执行与恢复
- retry budget：同一根因 2 次；第三次前 replan。
- staleness threshold：45 分钟或每完成一个 task 更新证据。
- stop condition：`pass | replan | split | blocked | abort`。
