# 负结果记录：20261117-task-diagnostics

## 已验证的负结果

| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-11-17 | 可复用本地 lessons 历史 | rg --files knowledge | 未发现 knowledge/L2-domain/lessons.md | 不虚构历史经验 |
| 2026-11-17 | 当前环境可进行宿主认证 | 检查 ~/codex 与 knowledge-provider.sh | 宿主与知识入口不可用 | 仅交付源码和已实际验证材料 |
| 2026-11-17 | 新诊断接口已存在 | 实现前 Trace/Task 验收 | 新 API/keyword/flag 缺失，两个入口均 exit 1 | 保留真实 RED，随后实现 |
| 2026-11-17 | 未被引用的 fixture 也属于读取集合 | 首次 Task GREEN 尝试 | 别名负例的测试前提错误，exit 1 | 通过额外真实 guardrail 引用纳入 read-set，未扩大读取或减少断言 |
| 2026-11-17 | AAR reference 可单独变化 | 原 Skill content 合同 | reference/template 字节不一致，exit 1 | 按原合同同步既有 template，不修改测试 |
| 2026-11-17 | 新 AAR 详述仍在 Profile 预算内 | d0d2b2d 洁净完整回归 | 101/102；唯一 footprint 组失败，两个 potential source 上限超出 | 只压缩重复 reference 及同步模板，不提高阈值，原失败保留 |
| 2026-11-17 | 知识 Provider 当前可执行 | 真实 knowledge-provider.sh context 调用 | exit 127，文件不存在 | 不伪造宿主 authority 或知识入库 |
| 2026-11-17 | checklist固定项可直接追加说明 | 当前change workflow verify | exit 1，治理器要求固定项精确匹配 | 保持原清单项，说明移至下方正文；不改治理器 |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| rtk proxy rg --files knowledge | 0 | 目录存在但无 lessons.md | 本记录及仓库 knowledge/ | repository | requirements.md |
| rtk proxy test -d ~/codex | 1 | 无实际宿主工作目录 | 本次环境观察 | environment | design.md |
| rtk proxy python -m unittest discover -s tests -p test_trace_summary.py | 1 | 实现前新 API 缺失 | evidence/implementation-observations.json:diagnostics-red-trace.log | deterministic RED | REQ-001 |
| rtk proxy python -m unittest discover -s tests -p test_task_evidence.py | 1 | 实现前新 keyword/CLI 缺失 | evidence/implementation-observations.json:diagnostics-red-task.log | deterministic RED | REQ-001 |
| rtk proxy python -m unittest discover -s tests -p test_task_evidence.py | 1 | 未引用 fixture 的别名前提错误 | evidence/implementation-observations.json:diagnostics-green-task.log | fixture diagnosis | REQ-003 |
| rtk proxy bash tests/test_skill_content.sh | 1 | 原字节同步合同拒绝 | evidence/implementation-observations.json:diagnostics-skill-content.log | static method | REQ-004 |
| rtk proxy bash tests/run_all.sh --timing-json full-timing.json | 1 | d0d2b2d 为101/102；1082源输入前后相同 | evidence/full-attempt1/summary.json | full regression | REQ-005 |
| rtk proxy bash tests/test_profile_context_footprint.sh | 0 | 压缩后6 tests通过，原两个Profile上限保持 | evidence/footprint-fix-observations.json | targeted fix | REQ-004 |
| rtk proxy bash scripts/devkit.sh verify --change 20261117-task-diagnostics --owner root-coordinator | 1 | checklist精确项文本不匹配，尚未运行源码验证 | evidence/workflow-verify-attempt1.md | change governance | REQ-005 |
| rtk proxy bash /home/agent/codex/scripts/knowledge-provider.sh context --cwd /workspace/scratch/d417066aafa8/llm_agent --query 'ADK 11.4.0 task diagnostics and replan replay source release' --task-type research --context-budget small --limit 3 --summary-json | 127 | 脚本实际不存在 | 本次环境原始错误与verification.md | unavailable host | REQ-005 |
