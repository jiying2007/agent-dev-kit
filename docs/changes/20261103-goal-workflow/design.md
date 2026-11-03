# 设计与边界

ADK 仅扩展 planning_state 的有界可选 work_in_progress，不改 canonical Execution Policy 引擎。新 Goal 技能作为 Codex 本地资产由 local/codex 维护：不复制 ADK 规划执行能力，不导入未提交上游镜像。

Codex CLI 用包内绝对入口固定 import root、保持调用 cwd；合同检查只验证结构与映射，不能证明证据或授权。运行控制继续使用原生 Goal 和现有 Execution Policy，不建立第三套执行引擎。

gros_compile 新增唯一精简 JSON 动态入口和有限批次合同；旧计划保留历史与完整验收，入口跳转但不删改历史正文。试点只改文档，不实现 AAC 或其他业务。

风险：既有 source/live dirty 需保留；实际旧线程不会自动加载新技能；预算提案不能冒充已设置；源码测试与 live apply、领域验收分开。回退仅撤销本次精确文件差异，live 使用受管 plan 备份。
