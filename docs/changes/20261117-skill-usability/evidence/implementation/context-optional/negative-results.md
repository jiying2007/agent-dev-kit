# T3c 实施负结果

角色：implementer；既有20项审查结果已冻结，自测不作独立review。

## Build 经验检索

按当前任务关键词 `Skill|skill|导出|optional|归档|任务包|task.package|v2|catalog|消费者` 检索 `knowledge/L2-domain/lessons.md`，得到文件不存在（rg exit2）。未引用或伪造历史经验。本次以冻结源码反例、U09/U10及v2澄清合同为依据。

## RED / GREEN

先新增专属 `tests/test_skill_consumer_usability.py`，测试读取真实发布命令、真实compiler输出、人类模板映射以及现有只读matcher/strict v2拒绝路径。模型行为仍为 not-measured。

首次测试误用 core profile，archive/planning 不在其闭包，产生3个测试入口错误；原始 `red-tests.log` 保留，不算这两项的有效RED。修正测试夹具为已有 team-core（包含本组全部 core Skill），未改生产 profile。仅将正确环境下的第二次 `red-tests-valid-profile.log` 作为产品反例。审查最初 core+optional 的导出只含16/20；原始 probe presence 如实保留，另做 team-core+optional 的20/20覆盖对照。

- 有效 RED：5项测试，11个失败，0个错误；缺catalog optional、缺source helper适用边界、缺archive handoff产物、缺人类信封映射与recovery说明。
- 首次GREEN尝试：16项中只剩archive两目标的工作流正文未明确写出“只读”（Goal已声明）；补齐局部责任说明后16项通过，原失败保留 `green-targeted-tests.log`。
- 首次组合ratchet：large-refactor超350B，保留 `ratchets-red.json`。缩短新映射引言和既有等价重复句后仍超53B，保留 `ratchets-intermediate.json`。最后精简重复闭合枚举及reference标题/引言，8个原ratchet全部通过，见 `ratchets-final.json`；没有提高限额、删除scope/owner/权限/hash或失败状态。
- 首轮通过日志 `green-final-targeted-tests.log` 为16项通过。最终源文件指纹与后续精确验证入口单独记录，实施者自测不算独立review。
