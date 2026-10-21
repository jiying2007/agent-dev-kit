# 负例与边界

## 原实现失败

基线为 ADK `42ae95d146ceb441ff91ea33dbbed581c33de305`。2026-10-21 首次八个回归测试有十八个失败子项，既包含真实 Broken pipe，也包含五个连字符名称被旧 grep 当作选项的案例；不能统称为十八次纯 EPIPE。原始 stderr 与 receipt 位于 `evidence/adk-regression-red-*`。

诊断实际管道容量为 65536 字节，profile 查询输出为 1085596 字节。原 quiet 模式和受控提前关闭 reader 均记录 `[pipeline, producer, consumer]=[2,2,0]`；完整读取为 `[0,0,0]`；无匹配为 `[1,0,1]`；匹配后上游失败为 `[23,23,0]`。collector 自己成功退出只表示状态记录完成，绝不代表原管道成功。

独立 Quality 审核补充发现 runtime boundary 的 handoff guard 列表遗漏，因此首版审核保持 HOLD，未据初版绿测批准发布。对应真实旧脚本的大列表回归失败，随后补齐相同修复。首次全量回归在 2026-10-21T01:26:21.659948Z 因该新增调用点主动终止，捕获退出 -15；其部分通过输出不计为完整验收。最终候选重新运行全量。

## 失败仍保持失败

未知引用、缺少真实 handoff guard、损坏 JSON、上游输出命中后退出 23 均必须失败。没有吞掉 OSError、取消 pipefail、重试刷绿或改变现场资格规则。

## 操作与环境限制

- 版本同步首次误用 wrapper 不支持的 `--by`，命令 exit 1 且未改版本；随后调用已读的 canonical `versioning sync-identity --actor ai/root`，七份版本投影正常同步至 8.0.37。
- 当前真实 `/root/codex` 不存在：knowledge-provider 实际 exit 127；apply 前的 canonical Hub 可用性预检实际 exit 2。没有伪造 Hub、改 HOME、安装 live 或宣称 Hub policy PASS；也没有形成 Provider 归档结论。
- 本机进程沙箱内 `ps` 返回 `fatal library error, lookup self`；对自己启动的测试进程只读检查经自动审批在宿主环境成功，随后仅停止该次已被取代的测试后代进程。
- 本机没有 ShellCheck 或 Python 3.8/3.11 解释器时，不声称其本地运行通过；正式受保护 CI 执行既有完整版本矩阵和 ShellCheck。

2026-10-20 的旧 aggregate 45 PASS / 6 FAIL 与后续单项恢复记录保持原样。本轮确证现存代码缺陷，不重建旧事件缺失的精确命令与 PIPESTATUS。Native、G22、长期现场及 Product M5 资格仍以各自真实材料决定。
