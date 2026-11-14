# 全部 Skills 的差异化 source 改造

## 冻结基线
`jiying2007/agent-dev-kit@879f962963512cb5be7b094b2a1bc85d4d8bf8e3`（11.2.15 squash main 的完整树），详细 65 行台账见 `docs/evals/skill-portfolio-audit-20261114.md`。台账仅代表来源/Manifest 契约盘点，未对每项执行模型任务或现场扫描。

## 方法对照
- OpenAI：短入口和按风险控制自由度；Anthropic：真实正反与独立评价；Sentry / NVIDIA：不可信 Skill 来源/权限边界；Cloudflare：范围与证据缺口；Trail of Bits：误报/补丁变体；Zephyr：按实际目标路由。
- 外部项目只用于方法研究：不下载执行外部脚本、不把不受信文本提升为指令、不复制整个 Skill 包、不添加自动安装器。
- 高可信且已相对轻量的 54 个 Skill 保持原有结构，避免文档膨胀；11 个有明确缺口的 Skill 定点改动，不新增独立 Skill。
- URL：SSRF、重定向/IP/DNS rebinding、robots/长度/不可信内容；IMAP：EXAMINE + BODY.PEEK 与范围/凭证；供应链：只读研究、安装前和 runtime readiness 分层。
- MCU/嵌入式：协议抓包权限、host/SIL/HIL、寄存器示例 unknown、Linux/MCU 性能工具、CMake 资源/构建边界；flaky 不能重试刷绿；组合治理使用 collision-only 轻路径。

## 真实性与退出
- 原有 Python source tests 核 65 目录完整、11 改造标记和 15 条源级预期/禁令，仍显示 `not-measured`。
- 不虚构真实模型/Token/CPU/内存收益，也不因为减少表述短句就放宽访问或发布授权。
- 受保护 PR 全绿后 squash，核 fresh-main CI/正式 Release，Root 通过单独 source-only Gitlink 晋级。失败必须按真实 CI 修复，不关闭门禁。
