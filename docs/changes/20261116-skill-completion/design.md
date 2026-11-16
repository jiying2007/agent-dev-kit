# 设计

需求：@docs/changes/20261116-skill-completion/requirements.md。

## 方法与边界

- 40 个通用/optional Skill 与 25 个嵌入式 Skill 分组深读，逐入口和直接资源保留基线 SHA256。root 统一核 manifest 集合和最终变更状态；保留项也给出当前依据。
- 原作者 Skill 只作不可信研究输入；优先能对应当前反例的具体方法。不上游照搬绝对硬件参数、未经评估的效果数字或新的权限规则。
- 并行包默认在现有正文说明最小字段；源仓模板仅在已核源码根且文件存在时使用。沿用现有按需 reference，不引入新镜像。Review 反馈 reference 删除重复快照片段，链接同目录已有的 `review-evidence-template.md`，保留目标选择和机械/语义结论区分。
- 数据获取父层透传结果的完整性和验证状态；成功数据与失败原因共存。成长复盘对齐 metadata/正文及 Skill README 的读取范围。归档先比较原 hash、当前内容与可信来源，已核实且获授权的变更才重算；未知差异保持未修复。这是明确的静态设计反例，不宣称发生过真实归档事故，也不新增归档工具或门禁。
- 已用真实 CMake 3.31.6 确认全部 `SKIP_RETURN_CODE` 测试仍返回 0；全 disabled 在同一工具下返回 8，保留此反证。CMake 合并互斥 preset/manual 分支到一个发布块，用参数数组共用 build/test，保持二选一、配置与后端身份。有效后端只执行一次 CTest，写入新建报告目录中的 JUnit，先输出报告路径并保留非零退出；内联 host Python 3 标准库读取同次 XML，实际 passed 为零即失败，skip/disabled 不能算通过。根元素必须是 CTest 的 testsuite；缺失/未知 testcase status 或 failure/error 即拒绝，不能被另一个 run 掩盖。明确 CTest >=3.21、此检查用 Python 3，纯消费不依赖 ADK Python。混合结果显式报告 partial，必需用例缺失仍阻塞任务；compile-only 不执行测试或 Python，也不要求 test preset 等测试专用变量。
- HIL/SIL 入口也保留同次 JUnit 证据及 passed/skip/disabled 的分开判断，用项目已核 runner/配置；不硬编码 `build/sil`，不要求另一个 Skill 已安装。它的命令退出状态与整项资格判断明确区分，不复制整套构建器或解析器。
- 本机核实的 CMake/CTest wheel 可用于新增结果语义用例，选择实际已有的 Unix Makefiles；既有 Ninja/多配置用例和 CI 缺工具 hard-fail 保持。新用例不是伪造 Ninja，也不把本机未跑的多配置项记为通过；具备工具的最终 CI 仍必须执行全部适用用例。
- 命令示例测试继续执行真实发布 bash 块，15 秒是整个块的工作预算。真实反例已观察到超时后输出未进入 traceback、sleep 后代仍运行；改为独立进程组，在超时处终止本次组、限时回收并输出已捕获的两流、预算、耗时和执行身份，不增加每阶段预算或重试。有界回收耗时单独报告，不作为额外执行时间，也不声称包含创建/回收的总壁钟严格小于 15 秒。CMake fixture 可用本地 bash trace 显示最后尝试的命令；生产 Skill 不强制开启 trace。新子进程测试可注入更短预算，但发布块调用保留 15 秒默认；实际旧超时根因与诊断机制分别记录。
- 减少重复表述为必要改动腾出字节；profile ratchet、已有内容断言及门禁保持。研究/原始反例放本 change，不灌入运行时入口。

## 职责

root 是需求/设计与集成 owner，不写实现代码；general 与 embedded 分别独占任务表指定实现和测试路径，不改需求/设计。research-review 保持只读，先审设计、再审最终来源和证据；不能自审自己的实现。实际写集在实现前冻结，有新发现先更新设计/任务。

回滚以本轮原子提交 revert 恢复 11.3.6 资产；保留历史失败与发布回执，不改旧 tag/Release。最终平台资格由真实 CI/合并/Release 对象给出，不倒填进冻结源码证据。
