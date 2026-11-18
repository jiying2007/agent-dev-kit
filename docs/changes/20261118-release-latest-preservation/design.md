# 历史发行补发保留 latest：设计

## 方法机制与来源取舍

复用 `.github/workflows/release.yml` 既有 `ci-reuse` 验证结果区分当前发行与历史补发。当前发行提供的 successful main CI run ID 必须对应可信 `workflow_run` 的 ID 和 head SHA；历史补发使用自身 source 的既有 CI 查询与全量回归路径。发布步骤只接受明确的 `true/false`，将结果传给 `gh release create --latest`，不依赖 GitHub 的默认 latest 选择。

问题来自本仓真实发行回执。保留原 exact-SHA tag、可信 CI 资格、历史 source 回归、不可变资产和摘要校验；不引入独立 latest 台账或由人工输入决定的权限开关。已有 release 的资产比较路径保持，未观察到的 artifact 命名冲突不作为修改依据。

## 资产归属与验证

修复属于 ADK 共享发行 workflow，回归进入原 `tests/test_release_ci_authority.py`，继续由既有 release-manifest 测试组执行。测试以离线 GitHub CLI 状态夹具运行实际 workflow Python/Bash 片段，观察创建命令与 latest 状态迁移；夹具不是线上发行证据。原 8 个版本锚点同步到 `11.4.4`。

Root 只消费新发行的 exact source，使用原 `scripts/promote-adk.sh` 生成 gitlink 和状态投影，并获得自己的消费验证。ADK 的成功不能代替 Root 验证；确定性发布测试不计为模型、Token/费用或真实宿主效果。

## 维护、退出与回滚

后续修改发行入口时复用本回归，保留 current/backfill 和身份负例。若候选验证失败，保留原失败并停止晋级；若新发行仍不对齐 latest，保留 Root 当前已验证 pin，沿受保护后续补丁修复。不删除、移动已发布标签或覆盖不可变资产，不以关闭补发、跳过门禁或放宽预算回避问题。跨工作流并发排序若出现独立证据，另立单一问题变更。
