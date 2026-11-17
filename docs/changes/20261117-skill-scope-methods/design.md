# 设计

以最小范围修复同一轮已确认的 Skill 适用性与方法精度。入口/参考文字优先替换、合并既有句子；不放宽 Profile 阈值或新增方法框架。

## 所有权与实现

- routing implementer：既有 canonical matcher/manifest/单测 Skill 适用范围与定向正反回归。先检查路由与直接 skill-trigger 两条入口，不用语言黑名单。
- method implementer：perf、storage、production pilot、artifact、growth、composition、URL 的既有入口/参考修正；从验收派生最小确定性方法与导出/命令检查。
- Root preparer：只读核 Root 当前晋级流程和证据格式；ADK 不可变 Release 完成后再接入。
- coordinator：需求/设计/任务、版本包装、回归整合、原始证据及发布；独立只读 reviewer 不改实现。

公共路由行为需实际 matcher 正反控；导出依赖用真实 compiler 的 team-core 两种输出检查；扫描用真实 rg 覆盖。纯措辞更正可用范围案例核对，不能仅靠关键词存在声称行为改善。URL/UBI 的方法控制只证明各自失败条件，不声称实际生产客户端/设备实验。

路由所需领域词优先放入既有 Skill frontmatter 的可选 implicit_context；由同一 canonical kernel 统一消费并校验类型。没有该字段的旧 Skill 保持语义；不在 Python 维护第二份 Skill/领域词表，不增加平行 IR。局部否定、显式域外和正常多句嵌入式任务都须有对照。

## 验证与体积

受影响共享路由/manifest 按仓库要求执行完整回归；先定向验证以定位失败。独立复审绑定具体 source tree、变更文件和 fresh 证据。原 8 个 ratchet 是源增长约束，不是实测 Token。任何失败先保留原始结果再判断。

## 发布与回滚

候选 patch 版本预期 11.3.13，包装前重新确认版本。使用当前受保护 PR、main exact-SHA 自动发布链；Root 仅消费已核验不可变发布，更新真实 submodule/lock/晋级证据，不变更历史资格。回滚使用前一不可变 11.3.12 与 Root 精确指针；不覆盖旧 tag/release。

已核 Root 当前实现是 source-only 两路径事务：仅提交 agent-dev-kit Gitlink 与 reports/current-status.md 自动投影；adk.lock 是忽略缓存，native Release attestation 由既有 integration-deep 验证，不复制旧式 promotion/M5 材料。
