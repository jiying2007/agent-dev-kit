# 负结果与边界

- 最终独立源码审查又复现三个 Markdown/sigil 名称拒绝绕过，以及 `-experimental` 被误当成同名 Skill 的问题。新增生产 matcher 测试先出现 23 个失败子用例。首次修正错误地在去空白文本上检查标识符左边界，使英文 `use name` 连成一个词；一次命令还误写两个不存在的测试模块，保留四个失败与两个启动错误。改为原始 casefold 文本上的精确标识符边界，仅识别有限 backtick / `$` / `@` 前缀，再使用原有否定规则；最终 47 项路由/内容测试通过，未扩大为任意自然语言理解。
- `4f9346e488a37926df560fa39ad8a275873e6c21` 的首次完整入口在独立发现后主动停止，退出 130；已完成 27 组 PASS、0 组 FAIL，没有生成完整 timing。保留原日志和中止回执，不计作完整回归通过。修正后对新的冻结源码从头执行完整入口。

- 基线 public matcher 对 `只做短文本问答，上下文工程`、`高风险审计要求直接看原文，跨会话恢复`、`单文件小改且上下文已充足，context planning` 均返回 `adk-token-context-governance`、`selection_group_promoted=true`；目标主 Skill 的三条 non_triggers 被绕过。对照 `上下文工程` 正常提升应保留。
- `knowledge/L2-domain/lessons.md` 不存在，不能宣称查到历史失败经验；改从已有变更记录恢复事实。
- `rtk` 未安装；Python 实际版本为 3.12.14。直接调用现有工具，不以缺失包装器制造假通过。
- 早期读取猜测的 `interactive-discovery.md` / `test_skill_v2_matcher.py` 路径失败；已用 `rg --files` 和引用搜索定位真实入口。失败不计为已审查文件。
- 新路由负例在基线全部出现实际错误匹配；独立复查又发现直接拒绝主 Skill 名称时仍能提升。新增中英文身份拒绝测试先失败，再将其接入既有 polarity、显式选择、routing、lexical 和同组提升。词法规则仍有范围，“并非”/双重否定等不能声称完整理解。
- 便携性测试首稿误用不存在的 `optional_skill` kind，已依据 `Manifest.all_assets('skill')` 实际接口修复；该接口包含 core 和 optional。去除 wrapper 后还暴露了旧测试只识别 `rtk bash` 的耦合，以及 llm_agent 脚本被误当 ADK 路径；改为可选 wrapper 匹配并明确外部 source root，未取消脚本存在性检查。
- 分发文本首稿超过原 profile 全部潜在源码预算；随后在相同 Skill 内精简重复正文/示例，不提高上限。八个 profile 的原 ratchet 预检通过。
- 版本推进时，未运行的历史 method campaign 仍计划 v11.3.4，原测试拒绝；保留原未运行身份后把候选更新至 v11.3.5，results 仍为空，不能把本轮合成记录或单次对话观察补写成该 campaign 的模型结果。
