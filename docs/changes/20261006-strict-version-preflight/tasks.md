# 任务与证据

- [x] 核实指定 worktree、分支基础与局部规则；基础 SHA 为 `b668712d3277ed1a4347e78ba83628b643a0c1e9`，初始工作区 clean。
- [x] 定向基线：`rtk bash tests/test_validate.sh` exit=0。
- [x] 负向基线：临时源码副本 `CONTEXT.md` 改为 `0.0.0` 后 strict exit=0/status=pass，quick exit=0/status=pass，而 release check exit=1，失败为 `version mismatch in CONTEXT.md`；复现验证与发布身份检查的差异。
- [x] strict 非 quick 复用现有版本身份 checker。
- [x] 补两个投影各自缺失/漂移的真实 CLI 消费者回归与 quick 语义回归。
- [x] 定向复验：修改后 `rtk bash tests/test_validate.sh` exit=0；现有 quick/strict 正例及强制 governance 失败负例继续通过，两个投影各自 missing/mismatch 的 strict 负例与 quick/strict+quick 正例全部通过。
- [x] 差异检查：`rtk git diff --check` exit=0；范围仅指定两个文件与本 change 三份文档，无版本/lock/CI 改动。
- [x] 核验独立 review 发现：copytree 保留 symlink 后直接 write_text 会追链接；fixture projection 修改及恢复均改为先 unlink 再创建普通文件，不写 source projection。
- [x] 与 reviewer 核验父目录 symlink 的 unlink 越界风险，增加读取及替换前父目录范围验证和拒绝负例。
- [x] symlink 隔离回归与最终修正后 `rtk bash tests/test_validate.sh`、`rtk bash -n tests/test_validate.sh`、`rtk git diff --check` 全部 exit=0；leaf target 字节不变且副本恢复为普通文件，外部父目录的读取/替换被拒绝且 target 字节不变。

本 change 不声明整体交付、live 更新或产品资格；真实模型、签名、发布与外部写均未执行。

- [x] 追加负向证据：主线程候选全回归 `/tmp/adk-next-strict-main-full-20261006.json` 为 96 pass/1 fail，唯一 file-mode gate 仅认 `.git` 目录，拒绝合法 worktree gitfile。本执行者定向复现相同 `not a git repository` 输出。
- [x] 当前候选基础已转到 `3bb4ce3356f6b2b13f3f6f72a3f4816af6e9b737`（主线程确认与原 b668 tree 相等）；原 strict validator 与 test_validate 文件身份在本轮保持不变。
- [x] 修正 Git toplevel 与 requested physical root 相等验证；新增真实临时 Git worktree 和拒绝负例，不修改正式 Git refs/index。
- [x] 追加 scope 定向复验：`rtk bash tests/test_file_modes.sh`、`rtk bash -n scripts/check-file-modes.sh tests/test_file_modes.sh`、`rtk git diff --check` exit=0。纯临时无 Git snapshot 保留 ambient inventory，从非仓库 cwd 执行同一测试也 exit=0。
- [x] 追加文件 hash 交接；完整回归由主线程执行，本执行者未重复 full。
- [x] 主线程冻结后完整 host 回归：97/97 PASS，exit=0；/tmp/adk-next-strict-worktree-final-full-20261006.json，sha256=6baa06e6ba929e8e64bec0e9729a4b4b92f91b317c52c5b6ebda6a4bb44d7ecc。
- [x] 独立 whole-diff 复审：spec PASS、quality PASS；唯一 non-blocking minor 为临时 worktree checkout hook 未关闭。随后只在 fixture 的 worktree add 增加 command-local core.hooksPath=/dev/null，从 /tmp 调用 test_file_modes.sh 与 diff --check 再次 exit=0。生产 checker 与 strict validator 字节保持不变；97/97 回执在该测试隔离微调前生成，不重新标记其快照。

## 下一轮交付准备（2026-10-06）

- 当前本地源码候选版本已前移至 7.14.1，manifest、pyproject、package version、version lock、README、CONTEXT 与 campaign ID 一并同步；CHANGELOG 记录修复、quick/inventory 权限边界及迁移。
- 本阶段先完成实际候选源码、全版本验证、组件构建及独立审查，之后才裁决提交门禁。用户先前的提交、推送、合并和应用权限继续有效；未通过必需托管检查不得合并。
- 上轮 GitHub Actions 37365201897 attempt 2 失败与 CodeQL runner 失败保留为独立外部阻塞；官方服务现为 major_outage，不盲目重试。#181 / Codex 来源升级及受管 live apply 未完成，未将它们标 complete。
- 7.14.1 最终矩阵使用 /tmp/adk-next-7141-parity-20261006.json；是否通过仅以实际终态和 receipt freshness 判断。历史 97/97 与最新候选快照不混用。
- 已规划回滚：保留 base=3bb4ce、原 b668 分支、pre-squash main 和全部 worktree；不清理用户 reference 或 ~/codex dirty，不调用真实模型。

候选尚未提交或应用；原 main 交付、真实签名 promotion 与 owner/product/runtime 资格均不由本记录推导。最终验证及 PR 事实记录在 source 外的阶段交接，避免测试完成后追加本文件造成源码快照漂移。
