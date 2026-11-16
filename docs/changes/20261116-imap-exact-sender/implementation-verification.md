# IMAP 完整发件地址方法实施验证

实施范围仅为既有 optional IMAP Skill 与 `tests/test_skill_imap_sender_methods.py`；聚合测试注册、ADK版本、Manifest、Profile预算与最终交付由parent整合。没有新增生产邮件客户端、协议服务器、依赖或Skill。没有连接真实邮箱或启动外部模型。

## 一手来源

2026-11-16读取以下规范的对应正文：

- RFC9051 §6.4.4：字符串搜索默认是子串，FROM搜索针对envelope的FROM字段；https://www.rfc-editor.org/rfc/rfc9051.html#section-6.4.4 。
- RFC5321 §2.4、§4.1.2：保留local-part大小写，域名不区分大小写；等价quoted形式按解析后语义比较，不能据此推广特定供应商的别名规则；https://www.rfc-editor.org/rfc/rfc5321.html#section-2.4 、https://www.rfc-editor.org/rfc/rfc5321.html#section-4.1.2 。
- RFC5322 §3.4、§3.6.2：显示名与mailbox地址分开，From是mailbox-list；https://www.rfc-editor.org/rfc/rfc5322.html#section-3.4 、https://www.rfc-editor.org/rfc/rfc5322.html#section-3.6.2 。

Skill新增独立的“仅完整发件地址请求”段，保留普通模糊请求、原精确时间分支、EXAMINE/BODY.PEEK/UIDVALIDITY和原预算约束。语义或头信息不足时保留成功项与未判定UID，不以地址匹配声称身份认证。

## 实际执行

执行器：CPython3.12.14；工作目录 `/workspace/scratch/fe8de3b42084/adk`。以下命令均通过已发现的 `/workspace/scratch/fe5385ca063a/verification-tools/rtk` 运行。

| 阶段 | 命令（rtk之后） | 实际结果 |
| --- | --- | --- |
| 源方法RED | `python3 -B tests/test_skill_imap_sender_methods.py`，Skill仍为1.0.4 | exit1；7个测试中6个行为控制通过，1个源契约测试含7个缺词subtest失败；不是ADK运行态bug复现 |
| 方法GREEN | 同一测试命令，Skill更新1.0.5 | exit0；7/7，0.003秒 |
| 原时间路径 | `python3 -B tests/test_skill_imap_time_methods.py` | exit0；7/7，1.527秒 |
| 定向差异格式 | `git diff --check -- optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md tests/test_skill_imap_sender_methods.py` | exit0 |

第一次RED的assertIn错误包含整份Skill文本；仅将断言失败显示改为缺词提示后重放RED，仍是相同7个缺词subtest失败。未更改判定条件，也未据此放宽验收。失败词为“完整发件地址、FROM、子串、local-part、别名、身份认证、模糊”。

7项测试包含：源码条件方法与旧只读边界；裸地址/显示名正确地址与显示名伪装/后缀域名对照；域名大小写/local-part/别名/quoted形式；缺失/重复/畸形头；未知地址语义；数量与头字节预算；普通模糊请求兼容。相同输入下错误子串方法接受全部4个样本，真实解析方法仅接受2个正向样本，避免“全部拒绝”伪通过。

测试中的selector是test-owned方法控制，使用真实标准库解析器；它只处理给定的headers和已证明覆盖的固定候选。计数/字节预算指这些已给定头字节，不是生产IMAP wire-byte限流实现。其通过不证明任意邮件格式、真实服务器、认证/只读副作用、native触发、泛化A/B或Token/费用收益。

## 受测文件身份与规模

于2026-11-16 23:41:54北京时间核验；这是未提交源码快照，不冒充最终commit或CI执行。

| 路径 | bytes | SHA256 |
| --- | ---: | --- |
| 原IMAP Skill1.0.4 | 3782 | b109548aceb24d3f978e92eb4706cc0845847c82a741d05810ded49f44f351b7 |
| 受测IMAP Skill1.0.5 | 4527 | 2bc927093f8a44a855b7b03d837e33b6d3b160e1e6a15db5f401ec0545cc3a80 |
| 新sender方法测试 | 7362 | 7e5c29f785aaf8d9e3c6dd595631cae924cb7e8e8f7263e996bea31b14c980f6 |

入口增量745字节，来自一个条件方法段、一行证据字段及版本patch。没有更改任何Profile阈值；原Profile预算尚待parent执行真实检查，不能由optional身份直接推断通过。独立审查、聚合/完整回归、不可变Release与Root接入也仍由各自实际回执决定。

## 独立审查后的解析异常修复

独立审查发现：符合4096字节fixture预算的600层嵌套注释头（1236字节）在CPython3.12.14的`message.get_all("From")`惰性解析阶段抛出`RecursionError`。原helper未隔离该异常，因而无法交付此前成功项。这是新test-owned示例的实际异常缺口，不升级为ADK生产邮箱漏洞。

新增1项回归，将正常项、100层和300层注释正向控制、600层失败项、后续正常项置于同一候选序列；整个序列少于4096字节，避免由预算跳过掩盖解析失败。

- 修改helper前先运行 `python3 -B tests/test_skill_imap_sender_methods.py ImapSenderMethodTests.test_parser_failure_isolated_between_successes_with_deep_positive_controls`：exit1，1项ERROR，`RecursionError: maximum recursion depth exceeded`，0.042秒。原helper未改变；错误发生于`get_all`，栈随后位于标准库`all_defects`递归。
- 最小修复将`parsebytes/get_all/addresses/groups`的解析区域限定在异常隔离块，仅捕获`HeaderParseError/ValueError/RecursionError`；该UID记`unparseable-from`、最终`partial`，继续后续候选。不捕获一般`Exception`，不修改解析器递归上限。
- 修复后运行 `python3 -B tests/test_skill_imap_sender_methods.py`：exit0，**8/8**，0.012秒；100/300层和失败项前后的正常项均保留，只有600层项未判定。`git diff --check -- tests/test_skill_imap_sender_methods.py`为exit0。

2026-11-16 23:45:32北京时间记录最终本地测试文件：8415字节，SHA256 `584b1719a107309306c8126617c2ff706e540cd67391cbbbb97432380ddfcbfa`。CPython3.12.14，递归上限实测1000。上表的7362字节/7项记录保留为首轮历史，不能再代表本次修复后的最终测试。Skill本身没有追加文本，4527字节及其hash不变；聚合和CI须按修复后文件重新核验。
