# 实施与验证

- [x] 基于冻结 v11.4.13 清单、八个 Profile 和 65 项源码完成盘点；未发现完全相同的 SKILL.md Blob。
- [x] 通过 GitHub 全量回归识别核心能力不可任意移出 Profile；恢复所有原始 Profile 顺序和闭包，不删除消费者断言。
- [x] 合并低风险 route 快路径与明确安装边界；缩短 Context 重复信息，保留高风险证据与回退。
- [x] 修复未执行真实模型试验的 candidate prereg 版本；继续标记 not-measured。
- [ ] 最终 HEAD Python 3.12 full regression、契约、平台/安全、CodeQL、评测打包、发布检查（由 GitHub 真实结果裁定）。
- [ ] 受保护 PR 合并、fresh-main CI、不可变 v11.4.14 发布（由原生工作流裁定）。
- [ ] Native Host 多轮任务效果、Token/时延真实对照：not-measured，不以当前源码 CI 代替。
