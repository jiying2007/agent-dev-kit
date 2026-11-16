# 验证与交付记录

## 已完成的源码验证

本记录追加于冻结源码之后，保留 tasks.md 的阶段快照。两个入口均为1.0.4，ADK版本为11.3.12。独立源码审查结论为 Spec PASS / Quality PASS，findings为空。

- 基线：`fad9d4d170a97c5dbb2c5261432fa2120bfcc3c9`。
- 精确远端受测源码：`384bdcdfac75881891bce795991b68fa46d9b9d6`。
- 受测tree：`627aabff2317705de46b010126edf3b57a443d1f`。
- 完整patch：451173 bytes，SHA256 `ae27a8e2e298f8f4e98290adba4f2e2d4609d5a3d29a1eea11edbac8172e4823`。
- 完整回归于2026-11-16北京时间22:44:42开始，22:51:02结束；实际耗时379.451354秒。审查完成于北京时间22:55:14。

| 验证 | 实际结果 | 证据 |
| --- | --- | --- |
| 精确受测源码完整回归 | 102/102，exit0，无超时，前后HEAD/tree/index/status一致且clean | execution-bundle内完整receipt、timing、stdout、stderr |
| 新方法回归 | fault6项、IMAP7项；独立重放13项PASS、0 skips | 独立probe receipt与full日志 |
| 旧合同兼容 | 与新增模块共同14项PASS，IMAP原只读/父状态合同另有2项PASS | implementation-diagnostic与implementation-imap-bundle |
| 区分力 | 4种scratch坏变体均被原行为断言拒绝 | 忽略命中、包含排他上界、偷换Date、补造时区的原始变体/输出 |
| strict与版本 | 现有strict及身份校验通过 | strict-final、version-identity、prereg-identity |
| 原Profile预算 | 8/8通过，阈值逐字未改 | delivery-inspection、profile-ratchets |
| 实际导出 | Claude Code / embedded-fullstack +显式IMAP optional；99文件逐一摘要匹配，两份正文等于源 | claude-export、adk-export-manifest及留存Skill |
| 独立源码审查 | Spec PASS、Quality PASS，findings=[] | independent-source-review.json/md |
| 规范review记录 | 51个源码/证据引用的现有validator校验通过 | review-evidence.json、review-validation.json |

冻结前的共同定向、strict和Profile回执按最终文件hash绑定，不追认它们曾在最终commit执行。完整回归与独立13项重放确实在上述精确远端commit执行。

## 范围、结果与限制

本轮分组复查23个其他Skill：2个增强、20个KEEP、1个OBSERVE。Manifest除版本外不变，仍65个Skill身份；未新增路由、默认Profile、运行时接口或依赖。fault入口3559→3558 bytes；large-refactor潜在完整源323320/323328 bytes，embedded-fullstack316438/316854 bytes。这里是源字节检查，不是Token或成本测量。

一次新上下文消费者只获得实际导出的两个Skill和准备任务：正确区分未命中、有限host恢复证据及资源恢复失败；时间/SLA未知。邮件保留101/102/104/106/107/108/201，排除103/105，202未判定，结果partial。该任务的无sender日级搜索列表由固定fixture推导，不是新的真实邮箱命令；没有成对基线、模型重复、native或泛化效果结论。

没有设备/HIL、真实邮箱/TLS/认证或实际恢复SLA测试。IMAP fixture的字节预算检查针对其内容，不冒充通用协议wire-byte限流器。两个改动均为有受控对照支持的方法增强，不是ADK现有运行态判定器漏洞修复。

## 可独立复核的证据

- audit-bundle：27个原始审计/探针及归档脚本文件，含全部原字节、bytes和SHA256。
- implementation-imap-bundle：13个原始实施文件，保留RED的真实范围、原版本测试与后续元数据前移边界。
- implementation-diagnostic：原始命令、RED/GREEN、版本、预算及导出证据。
- execution-bundle：28个完整回归、消费者、独立probe/变体/报告和打包脚本文件。
- source-bindings和original.patch：45个冻结路径的完整身份与原始完整差异。

gzip+base64文件可逐项解码后核验长度与SHA256；源码审查报告和typed记录也保持独立引用。original.patch原样保存Git差异标记，包括空白上下文行，不为文本外观清理原始证据。没有修改既有格式门禁或产品阈值。

## 后续交付观察

此次追加仅包含验证说明与证据；增量包装审查另记在evidence/independent-packaging-review。受保护PR/main CI、不可变Release和Root source-only接入必须取得各自实际回执，不能由上述源码审查预先宣称成功；最终观察写入对应PR说明及交付答复。Root接入仍保留历史promotion证据、attestation与M5原资格，不刷新真实运行态。
