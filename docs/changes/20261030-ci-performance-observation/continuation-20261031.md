# 2026-10-31 续行：真实 timing 的严格读取

## 原因与范围

本次恢复既有 PR #228，不新建竞争分支。旧实现用正则读取 timing 字段，会受 JSON 排版、重复键、小数和嵌套字段影响；这违反原 requirements 中无效 timing 必须明确失败的验收。

复用现有 `strict_json`，新增内部 typed reader `performance_timing.py`；原 `check-performance-budgets.sh` 仅消费其验证后的模式、整数耗时与预算。保持公开命令和报告字段、600000 ms full 预算、report-only/strict 区分，不新增硬门禁或运行真实模型。解释器特定预算优先于 default，不依赖数组顺序；非法或重复预算不得生成成功观测。

## 验证

从 GitHub 原始 v8.1.3 发布 artifact 12908841659 恢复隔离源；ZIP SHA256 `b442ceb2a488cd90b413747f394f260056c650004b5b90e69c0c09a088da232f`，tar SHA256 `12ee750f61d92903f130ed1fa8940d6d72719644da3ab288d6cbfb322a6102f5`。本次只在对应脚本/测试覆盖层运行定向验证，未将这个发布源镜像冒充完整候选 Git checkout。

Python 3.13.5 本地 `test_performance_budgets.sh` PASS：保留既有正常、strict 超时、report-only 告警、full timing 和缺失输入断言；新增 4 个排版/顶层选择、21 个严格解析拒绝、6 个 shell 失败报告、整数边界及 6 个预算选择/歧义案例。两次早期有界验证超时已保留，随后把相同解析拒绝的重复进程启动合并为直接 typed reader 测试，所有断言保留，完整定向测试通过。bash 语法和差异空白检查通过。Python 3.13 仅为本地开发证据，不新增项目受支持矩阵；最终 3.8/3.11/3.12 与完整候选以新 HEAD 公开 CI 为准。

## 审核与交付

用户已在上一轮明确允许本批独立审核与正常交付，本轮再次要求继续。实现者自检不是独立审核；现有 Harness 旧回执不改写、不放宽。独立审核需绑定新源码、原始政策和实际执行，然后由受保护 PR/main、不可变发布和 Root 精确提升分别闭合。G21/G22/LTA 和产品资格仍需各自真实证据。

当前容器没有 rtk、活动 `~/codex` Knowledge Provider/Execution Policy 或 `knowledge/L2-domain/lessons.md`。记录为本地环境 NEEDS_REVIEW，不声称完成 live 安装、Owner/现场验收或外部运行策略门禁。
