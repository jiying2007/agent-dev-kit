# Skills 失败路径与方法复审

## 目标与基线

继续用户授权的全部 Skills 深度优化，从已发布 v11.3.9 / `80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b` 开始。对现有 65 个 Skills 重新逐项审查，并结合固定来源寻找真实、可验证的方法缺口；有实质改进时完成实现、独立审查、发布和 Root source-only 接入。

Root 基线为 `096a03b0e91f13fa4d5c5250e4211644b9bff493`。沿用本会话已授权的分支、PR、受保护合并与 source-only 接入范围；缺少宿主 `~/codex` 时仍如实标记 unavailable/not-run，不修改或伪造门禁。

## 验收

1. 34 个通用 core、22 个 embedded core、9 个 optional 的逐文件审查清单与 Git 跟踪人口相等；每个文件绑定 blob、SHA256、字节数和实际阅读范围，每个 Skill 有处理决定及依据。
2. 外部发现使用公开搜索，技术判断回到第一方仓库或官方规范；采纳候选绑定固定 commit、具体文件、许可、阅读范围与采用/拒绝理由。检索覆盖范围如实报告，不声称穷尽互联网。
3. 只落实由反例或明确消费失败支持的缺口。实现前将选定问题、预期行为、影响和可执行验收冻结到本目录，不以扩写字数、增加 Gate 或重复 Skill 代替改进。
4. 有行为变化时验证原失败、正常控制与必要反例；工具/环境不可用、原始失败和修正重跑均保留。不把关键词出现、host 算术或合成任务冒充模型效果或设备资格。
5. 原有 Profile 预算和保护检查不放宽；实施源码由另一位只读 AI 完成实际 Spec/Quality 审查，审查结论绑定准确源码与证据。
6. 发布绑定精确 main 提交；实际下载正式资产核对摘要和契约。Root 接入使用现有两文件 source-only 事务，完成本轮跨仓 attestation CI、完整回归和合并后检查。

## 非目标

不新增平行技能注册表、通用流程框架或资格体系；不整包移植外部 Skills。无外部付费模型调用、Codex/Work CLI 或 Cloud agent 作业、真实设备写入、邮件发送、定时巡检。无新的 native/runtime、RTOS/HIL、M5、现场、Token 或费用收益声明。

## 范围冻结记录

2026-11-16：三组已完成 65 个 Skills 的全文复审，以下五项由当前源码和受控反例确认，现冻结为实施范围；尚未取得修复后正式验证或发布结果。原始探针保留在同名 scratch 材料中，稳定后仅复制必要证据。

## 已确认缺口与行为验收

### F1 扫描内容泄漏

`adk-security-supply-chain` 的 network/license/write/runtime 候选扫描及既有 runbook 会通过 `rg -n` 回显匹配行，合成凭据可随无关风险关键词一同进入工具输出。所有初筛仅输出候选路径，后续内容审查须明确范围并脱敏；保留原有覆盖声明和错误诊断。验收实际提取并执行发布命令：同一行中的合成 sentinel 不出现在 stdout/stderr，风险候选路径仍可见，无匹配 exit 1 与读取错误 exit 2 不被吞掉。此验收不证明所有文件名或任意真实秘密都自动脱敏。

### F2 采样中断后继续调用

`adk-test-flakiness-triage` 的有界 helper 将子命令报告的 130/143 当普通失败，继续创建第二、第三轮并将最终退出码变成 1。约定这两种中断/终止状态在记录已得日志和退出码后停止，保留相应退出身份，不再调用下一轮。验收分别覆盖显式 exit 和子进程自发 SIGINT/SIGTERM；130/143 只产生一轮记录且没有 run-2，普通 0/1/9/124 继续按原有有界采样约定执行。不得据此声称父进程、完整 process group 或真实用户取消传播已经验证。

### F3 CMake 构建身份漂移

`adk-cmake-cross-build` 现有命令可在原 binaryDir 把 toolchain A 改成 B；真实 CMake 3.31.6 configure/build 均成功，cache 新路径为 B，但 CMakeSystem 与实际编译仍使用 A。强制重编译控制也复现。复用前必须核已有 toolchain/编译器/target/sysroot/generator/configuration 的真实身份及证据；身份变化或旧身份无法证明时选择新的任务自有 binaryDir，保留旧日志/配置，不删除或硬改旧 cache。验收包含同 A 重配、A→B 原目录反例、强制重编译及新目录 B 正常控制，并通过新消费者任务验证方法使用；host probe 不代表目标 ABI 或硬件执行。

### F4 Schema 组合与方言

`adk-interface-contract-design` 无条件要求 `additionalProperties=false`，在 allOf 子 schema 封闭时会误拒合法扩展字段；旧 draft 下仅改为 `unevaluatedProperties=false` 又可能放过未知字段。契约须声明消费者实际 dialect/支持子集：同层闭合保留 additionalProperties；仅支持的现代组合边界可使用 unevaluatedProperties；旧/窄子集采用同层展开或拒绝不能表达的契约，不静默放宽。验收用真实 validator 检查合法输入、未知字段、缺字段、错类型和错枚举，并保留旧方言误放行反例。

### F5 空审核模板预填通过

`adk-parallel-agent-governance` 的默认任务包实际引用并导出一份 Completion Review 表：5 行 Evidence 空白而 Result 预填 pass。空表默认使用现有未执行/待验证语义，逐项有证据后才填 pass/needs-fix/blocked。验收解析实际导出的表格，所有空证据项不得预填通过；不新增审核 Gate、状态协议或审批要求。
