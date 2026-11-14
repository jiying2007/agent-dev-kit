# 已观察的负结果与边界

## 原本地先导保持不变

前次本地OpenCode/Ollama先导在模型manifest下载阶段因宿主网络不可达停止，model_runs=0；其候选仍是11.3.0/4f77f795。已保存证据包SHA256为`6b5a76779320f45422ca4a06dfa394fff85106d352b65e7fbea56da7aa6018ca`。本实验使用独立公开宿主和11.3.1/c57候选，不覆盖该记录，也不把静态导出或服务健康检查算作推理。

## 规则与历史检查

草案曾将主动协调脚本放入docs/changes。独立审查指出根规则要求新增Python工具进入typed core，已有只读审查探针不足以构成豁免。root据此修订本次合同，将执行职责放入两个typed core模块、测试放入tests；不修改根规则，不新增产品CLI或正式版本。

按R1.8实际查询`knowledge/L2-domain/lessons.md`中的OpenCode、Ollama、Docker、容器、任务证据及实效关键词，文件不存在，查询exit=2；没有假定存在或编造历史经验。

## 草稿中发现的证据与预算缺陷

独立审查发现任务执行后若inspect/logs/remove抛错，旧草稿可能仍发布空条件和model_runs=0。这是记录逻辑缺陷，并非实际发生的模型试验。修复要求在启动前登记尝试，异常收尾保留possible-inference及unknown状态，并以启动后的故障注入测试验证。

旧草稿只有各子命令timeout，累计上限可能超过30分钟job并丢失收尾证据。冻结设计改用首步起420秒准备、1140秒成对执行预留、26分钟协调截止及4分钟最终收尾；两条件各300秒的推理预算不变。最终修复是否通过以冻结源码的实际测试和独立审查回执为准。

## 独立的无推理配置探针

2026-11-14T15:26:49Z起保存了一份当时的原生配置快照（4143 bytes，SHA256 `7411cefff349fab60439f9f4d0260216a19cc48a7ec9c2c57770e43735feea87`）。首个本地断网隔离检查被宿主拒绝：`bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted`，exit=1。错误stderr SHA256为`31c2cb0dffdeb9049fa2269e24af62df15e4161d4f752a648faf9630259725fe`；结果记录SHA256为`18fb67074daefe5508ab38fa2ca543eaad1e3199cd982d40a6f635fd94c78508`。

OpenCode本体、Ollama和模型均未启动；当前配置解析、session命令与Docker原生资格均not-run。没有去掉断网设置、修改权限或重复该路径。官方源码与历史CLI帮助仅支持配置/入口选择，实际Docker接受性仍由本实验job的无推理preflight判断。上述快照是明确的历史探针身份，不能替代最终源码的配置摘要。

## 结论范围

确定性合同测试和源码审查只验证协调器的实现。它们不证明原生Skill已加载、模型任务已完成、usage完整、真实Token/费用降低或消费者门禁已满足。模型任务只有实际job执行及独立原始证据审查后才能报告；尚未执行的步骤保留not-run。
