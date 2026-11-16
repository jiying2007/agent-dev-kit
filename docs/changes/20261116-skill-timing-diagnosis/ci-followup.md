# CI 跟进：Git bisect 证据解析兼容

## 故障与范围

PR #275 源码 `bc2f4b2ca3bbef2cb5515322048a144639e79004` 的 [CI run 43812320483 / job 133116507717](https://github.com/jiying2007/agent-dev-kit/actions/runs/43812320483/job/133116507717) 记录 Git 2.56.1；完整回归为 101/102，失败组的 152 个 unittest 中有 3 个失败。

两项唯一裁决案例的 `git bisect log` 已输出目标提交，但旧解析器只识别 `# first bad commit: [sha] subject`，没有识别实际 `# first 'bad' commit: [sha] subject`。歧义案例已非零退出并输出两个候选，随后因断言只接受 `The first bad commit could be any of:`、实际输出 `The first 'bad' commit could be any of:` 而失败。基础设施中止与 oracle 退出码案例在原 CI 中通过；原有终局否定断言仍只覆盖无引号形式，存在漏检风险。

本跟进仅修复 `tests/test_skill_bisect_methods.py` 对这两种已观察格式的证据解析。保留 good/bad/untestable、unknown-abort、准确目标 SHA、skip、非零退出及歧义候选断言。终局仍要求退出码为零且恰好一个记录；同一 SHA 重复出现也不能通过。生产 Skill、CI、门槛、版本及原审查记录不变。

## 验证计划与证据边界

- 先在本地 Git 2.52.0 记录原有五项真实隔离 Git 验收；加入已观察日志形态与缺失、重复、非零退出、误终局等回归，记录修复前 RED。
- 终局正反断言共用两格式 matcher；歧义标题仅接受完整的两种已观察标题。定向运行同一文件取得 GREEN，并核对 diff。
- 本地不运行 Git 2.56.1，不以日志形态回放冒充新版 Git 执行；新 head 的完整回归、独立审查与 CI 由主 PR 流程重新执行。

`knowledge/L2-domain/lessons.md` 不存在，关键词检索返回 exit 2；没有可引用的历史条目。原 CI 原始日志指针为 `/workspace/scratch/fe5385ca063a/round2-pr-first-regression.log`；实际命令、UTC 起止时间、源 SHA 与文件 SHA256 追加到 `/workspace/scratch/fe5385ca063a/round2-ci-parser-fix.json`。本记录由本次实现者维护，不替代独立审查。

## 实际验证

2026-11-16 本地实际环境为 CPython 3.12.14、Git 2.52.0。以下均由同一证据 runner 执行，源 HEAD 保持 `bc2f4b2ca3bbef2cb5515322048a144639e79004`，工作树中的被测文件另以 SHA256 绑定。

| 阶段 | UTC 开始—结束 | 真实结果 |
| --- | --- | --- |
| 原始基线 | 05:57:38.091428—05:57:39.183294 | 原有 5 项通过；原始日志实际使用无引号格式。 |
| RED | 05:58:43.196613—05:58:44.319488 | 10 项运行，8 个子断言失败，0 error；暴露带引号正例、终局否定漏检、混合格式重复及不完整歧义标题问题。原有 5 项仍通过。 |
| GREEN | 05:59:05.977494—05:59:07.153639 | 同一文件 10 项全部通过，0 failure / 0 error；包含原有 5 项真实 Git 验收与 5 项证据格式回归。 |

终局 matcher 先识别两种裁决记录，正例再检查恰好一条记录及完整 40 位 SHA；否定路径用相同 matcher，缺 SHA 的终局前缀也不能漏过。缺失、同格式重复、混合格式重复、不同提交多终局、截断 SHA、残缺引号，以及退出码 1/125/128/255 搭配终局的反例均被拒绝。歧义标题使用整行匹配，保留两个准确候选与非零退出的真实 Git 检查。

被测文件 SHA256：

- 原始基线：`a413b9fccf6dce8abc236a44554c100c69a0db2d5a304009a592040409daca74`。
- RED：`e1f0e125bc70aa49be453b34f297b6550f83a2a4c4b39d90c48e1d034141be32`。
- GREEN：`f8cb68ec55b1898842fb482958f640bcf1d17bf02da974e876fe491e8b895eee`。

原 CI 日志为 59,412 bytes，SHA256 `aa4a2bf14b427d2b4dd216308a70564d40a57cbf55cc4be4c697c47cb8bc35e2`。`round2-ci-parser-fix.json` 保留每阶段的完整实际命令、时间、stdout/stderr、每个隔离 Git 命令回执及所消费 Skill reference 的 SHA256。未在本地运行 Git 2.56.1；本记录不把形态回归或原 CI 中尚未执行到的后续断言算作新版 Git 验证通过。新 head 的完整回归与 CI 仍由主 PR 流程承担。
