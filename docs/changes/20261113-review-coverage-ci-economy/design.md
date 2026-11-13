# Skills 质量闭环与 CI 任务经济性设计

## 既有能力与缺口
ADK 11.2.13 已有 whole-diff review、快照和独立审核，也有 Level 0/1/2 TDD，但未明确要求大范围 Review 的未检查区域，也没有独立列出安全补丁的同根因变体。嵌入式工具例子包含非所有 MCU 适用的 host/Linux 命令。全套 102 个 Shell 用例的 catalog/content/SOP 检查排在后段，发生过 101/102 通过、仅描述投影失败的 CI 回执。

## 最小改法
1. 在现有 `adk-code-review-loop` 入口加条件标记，详细 coverage ledger 和 post-patch 验证下沉其既有 references，不新增主 Skill/新审查权威。
2. `adk-test-strategy` 仅针对高风险补丁启用原始失败/变体/合法行为验证，目标代码须已授权且隔离，不将 source/check 假冒实际执行。
3. `adk-static-analysis-c-cpp` 与 `adk-bsp-analysis` 使用目标平台条件分流，保留 vendor-specific 工具实际可用性检查。
4. `tests/run_all.sh` 只移动单次执行顺序；full 保持 102 个，quick 60→61，未增加新的 workflow 或 CI 并行 runner。
5. 沿用 `docs/evals/skill-method-parity.md` 与 `agent_dev_kit.effect_trials.compare_effect_trial_file` 准备真实 A/B，不能在缺 native trace 和实际 Token 用量时声称成功。

## 参考（方法借鉴，非依赖与源码复制）
Trail of Bits `fp-check`、`post-patch-validation`；Cloudflare security-audit-skill；Zephyr agent skills；Sentry prompt optimizer；Anthropic skill-creator。仅抽取证据方法，保留 ADK 当前 Manifest/authority、source-to-live、发布与安全门禁。

## 质量验证与撤销
新增 13 个 source-only 期望/禁止用例及 Python 契约测试，由已有 `test_skill_content.sh` 注册。受保护 PR 的严格、全量、安全检查必须成功。真实模型测试仍 not-measured。若失败仅修受影响代码/测试；回滚单独 revert PR。
