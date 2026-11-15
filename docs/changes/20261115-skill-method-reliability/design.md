# 设计与影响

## 边界

前序 [PR #267](https://github.com/jiying2007/agent-dev-kit/pull/267) 已在 8 项必需检查通过后正常 squash 合并为 `1282c78b145afca670cf8e5733d80bd3c61f5cfb`。新实现所在独立 worktree 已对齐这个内容相同的 main tree，原修改保持。当前候选为 11.3.3，以单独 PR 送审。发布顺序沿用既有 main CI → promotion → annotated tag → canonical release，前序版本发布完成后再合并本候选，避免使前序 promotion 的 current-main 绑定失效。

前序 11.3.2 已完成主线 CI 与 canonical release，annotated tag 精确指向上述 main；其实际事件、必需检查和 GitHub 报告的制品摘要保存在 [前序交付观察](evidence/predecessor-release.json)。本候选仍须自己的完整验证和交付。

## 实现原则

- current-state 的字段约束只保留一个共享实现，两个公开消费者继续负责其各自文件读取、错误码格式、计划依赖和输出。复用现有 typed core，不复制状态权威；调用点先检索。
- 发布示例显式接受已核实的 baseline 或首发选择，先得到完整真实历史再人工分类。不添加自动发布程序，不把任意最近 tag 当正式版本。
- flaky 的统计方法解释 observation、failure、error、skip 和 missing 的区别；有界重复示例直接调用已审查的命令数组，不用 eval，不隐式扩大重跑或安装范围。
- 专业命令只作最小必要修正，并保留工具、目标与证据适用条件。涉及 CTest、抓包、地址重定位的反例使用隔离的真实工具与合成输入，不访问设备或实时网络流量。
- 主文保持任务入口，长示例只在既有 references 中按需加载。优先替换错误段落而不是叠加规则。
- Artifact 与接口候选扫描只对齐已有实际行为，不创建新状态机或新的通过标准。

## 验证与回滚

共享代码用公开 CLI 的边界与重复值反例，保持原正常、拒绝、输出大小和无副作用测试。命令文档直接提取最终示例在临时 Git 仓、合成日志、离线 pcap 和最小 CMake 工程执行；不能用新增关键词断言冒充方法执行。

复用既有测试入口承载必要回归，原 full suite、静态 CI 和 profile 阈值不放宽。工具缺失须保留 not-run/环境说明，不将缺工具算成功。独立 reviewer 只读核验冻结源码、原始结果和限制。

回滚通过回退本候选；无数据、安装或 Manifest 身份迁移。新增拒绝只针对原 `resume` 已拒绝而 `state-check` 错误接受的状态，旧合法状态继续通过。
