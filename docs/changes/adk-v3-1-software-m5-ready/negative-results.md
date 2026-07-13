# 负结果记录：adk-v3-1-software-m5-ready

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-13 | release rehearsal 只接受单根目录 archive | 对真实 3.0.0 平铺 source archive 执行 rehearsal | 失败 | 与现有 builder 输出不兼容；改为只接受经过安全校验的平铺或单根两种明确布局 |
| 2026-07-13 | 使用系统 setuptools 45 做 no-isolation wheel | 构建并检查 wheel metadata | 生成 `UNKNOWN-0.0.0` | 不满足 `setuptools>=61` build contract；制品被拒绝，改用隔离 build/runtime venv |
| 2026-07-13 | matcher 用“命中数 + 首次位置”统一裁决歧义 | 运行 fallback matrix 和 60-task deterministic suite | 两轮分别误路由 brainstorming 与 HIL 测试策略 | 通用启发式会破坏既有语义；恢复 specificity 排序，在 manifest SSOT 显式登记复合意图 |
| 2026-07-13 | 仅用调用次数注入 export replacement 故障 | 新 writer lock 加入后运行 product maturity test | 注入点命中 lock metadata 写入 | 全局 `os.replace` 调用序已变化；改为按 source/destination 路径精确注入 |
| 2026-07-13 | 直接在 source archive 中包含 rehearsal report | 分析 report 写入 candidate SHA 后的下一次构建 | 形成 SHA 自引用，无稳定固定点 | 生成型 rehearsal/runtime/timing/campaign evidence 明确排除出 source distribution，由 checkout 和根仓证据链管理 |
| 2026-07-13 | 在 `return` 对象上机械追加 rehearsal report hash | product maturity release build 回归 | 补丁误命中 `build_release` 返回路径，build 返回 `None` | 立即修正为两个显式 result 返回路径并保留回归；不接受未跑测试的机械补丁 |
| 2026-07-13 | 只保存 campaign 汇总 report 即可支持 M5 | 根仓 certifier 独立审查 | 汇总自哈希无法证明 720 条原始结果存在 | final M5 强制保存 frozen plan、tasks 与 720 raw results，并逐项重算 record/evidence/report hash |
| 2026-07-13 | 只检查 field metric 字段存在 | synthetic certifier 负例 | 低 success rate 或非 approve decision 仍可能满足字段完整 | policy 增加 metric type/range/version/enum contract，certifier 按语义验证 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash tests/test_match_effectiveness.sh` | 0 | 25/25，含子代理/驱动复合意图 | terminal output | test | `matcher.py`、`manifest.json` |
| `rtk bash tests/test_fallback_sunset_matrix.sh` | 0 | 14 rows，replacement score 58/70 | terminal output | test | fallback routing matrix |
| `rtk bash tests/test_software_m5_ready.sh` | 0 | campaign、lock、apply/rollback、timeout、receipt integrity 通过 | terminal output | test | software M5-ready contracts |
| `rtk bash tests/test_product_maturity_v3.sh` | 0 | export 双重故障恢复、atomic archive、release/install 回归通过 | terminal output | test | product maturity v3 |
