# 负结果与环境边界

- 当前源码基线为 4f77f795ecfba3e6bb1e167eb27cb84cca796845 / 11.3.0。审计者实际复现同名同摘要 Skill 在第二 attempt 再次加载时抛出 `task evidence: duplicate or invalid skill exposure`；原有重试测试未包含 reload。后续保存 RED/GREEN 原始命令结果，不将此输入标为真实模型记录。
- 同名过程检查在 pass→pass 和 failed→pass 下也被误拒绝为 `duplicate process guardrail`，即使 event_id 不同且 seq 连续。修复必须保留早期失败，不能通过后一次检查覆盖。
- 当前执行环境实际未找到 rtk；不创建伪装包装器，不把缺失报告为已安装。只读核查与必要确定性复现使用已有 Python/Bash 入口，工具状态保持 unavailable。
- `knowledge/L2-domain/lessons.md` 不存在，未命中可复用历史条目。
- 当前无 Claude Code、OpenCode、Ollama 可执行程序；`/usr/bin/dot -V` 返回 Graphviz 2.42.4。无真实任务观测时不声明原生加载或收益已测。

## 环境修复

- 随后从官方 rtk-ai/rtk v1.2.0 发布下载 OSS 独立CLI，验证归档 SHA256 `a28407dc13038bdc9c2a1f5a047b0c636e0c1d495b15523576e2adb992a06a17` 后安装到本任务工具目录；实际版本输出 `rtk 1.2.0`。未安装代理、hooks 或全局模型配置。后续 shell 使用真实 `rtk bypass` 保留完整证据输出。
- 第一条完整类型分析命令按CI读取了 `mypy` 可执行名，但目标安装目录不在PATH，启动时得到 FileNotFoundError，未执行类型检查。随后用同一Python的 `-m mypy` 与原始CI参数、新缓存和 `MYPYPATH=src` 修正调用方式，不删减检查入口。
- 单独调用 `tests/test_promotion_evidence.sh` 时，本地未安装当前源码包且入口不自动设置 PYTHONPATH，出现 ModuleNotFoundError；保留该失败记录，再显式使用 `PYTHONPATH=src` 执行同一脚本。CI 的既有流程先安装当前包；本次未改脚本或放宽验证。
