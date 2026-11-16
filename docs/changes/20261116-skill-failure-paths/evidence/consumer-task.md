# CMake 消费者任务

在 `/workspace/scratch/fe5385ca063a/round3-cmake-consumer/project` 完成 `toolchains/release-b.cmake` 的 Debug、Ninja、host-unit 构建，并交付实际程序、CTest 结果和可复核构建证据。项目已有 `out/default` 构建及记录，来自 `toolchains/release-a.cmake`。本次不修改源码或 toolchain；构建并行度为 1。

只使用本任务、项目文件及 `/workspace/scratch/fe5385ca063a/agent-dev-kit/skills/adk-cmake-cross-build/SKILL.md`，不要查阅其他审计、实现、测试、旧对话或报告。可以读环境工具版本。根据 Skill 自行决定操作与交付内容，不向其他 Agent 请求方案。

所有 shell 经 `/workspace/scratch/fe5385ca063a/verification-tools/rtk`；CMake 所在目录为 `/workspace/scratch/771b38332ec2/domain-audit-tools/cmake-wheel/cmake/data/bin`，Ninja 在 `/workspace/scratch/fe5385ca063a/verification-tools`。需要写脚本或说明时用 apply_patch。允许写入的范围仅为本任务目录 `/workspace/scratch/fe5385ca063a/round3-cmake-consumer`，不改 ADK 仓库，不运行 Git 写操作，不调用付费模型或原生 CLI/Cloud 作业。

请将实际命令、退出码、时间、原始 stdout/stderr、交付文件及摘要、必要限制写到任务目录下 `consumer-response.json`，并保留原始日志；正文说明你的选择与实际结果。不要把本次主机构建说成板端或模型对照测量。
