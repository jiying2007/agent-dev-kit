# ADK 11.3.13 独立 Source-change Spec / Quality 审查

## 最终结论与精确身份

**Spec：PASS。Quality：PASS。** 结论限本报告绑定的 source-change：29 个变更的生产/测试/说明/包装文件，以及 requirements、design、tasks 三个变更合同。三个发现均已修复并复验，没有未关闭的源码缺陷。验收 10 的精确提交 CI、发布和 Root source-only 接入仍由后续实际门禁完成；本报告不是整体交付完成证明。

审查者是 `/root/independent_source_review`，包装部分由 `/root/independent_source_review/packaging_review` 独立审查。两者均未实现被审变更；所有报告、隔离反例和导出仅写在本审查目录，未修改被审工作树、index 或 refs。所有 shell 均经指定 rtk；保留完整输出时使用 bypass。

| 身份 | 值 |
|---|---|
| Baseline | `0973b9dce75e7bde289a9915fc58dfd53cb79b0d` |
| Canonical source target | `66df0ce7092aabbbd05411ef2950cc9ee59a3592` |
| 同内容本地候选 | `5d62b7e3da38ac7c9571cfd32707d9d2f4410ff8` |
| 完整 tree | `081cddd941f16a98aee76014998856bd33799610` |
| 原始 binary diff SHA256 | `7ce4b25c24f399c92998b405acd57f25fb192282173bd436bab57e52bea0030a` |
| 证据收齐时间 | `2026-11-17T02:44:27.097228+00:00` |
| 最终审核时间 | `2026-11-17T02:44:27.097238+00:00` |

实际读取本地已 fetch 的 canonical Git 对象，确认 parent 为 ab5ec7、merge-base 为基线，并比较 local/canonical 的完整 tree 与 base..head diff 原始字节，均一致；工作区 clean。此前 r2 运行的 local78ee2c 与 remoteab5ec7 也具有相同 tree/patch。不同 commit 身份始终分别保留，未将等价树说成同一 commit。完整记录在 `raw/source-final-bindings.json`。

## 完整回归与修复复验的边界

**本地最后一次完整 102-suite 运行是 FAIL，不能改写为通过。** 干净的78ee2c在 02:31:18–02:37:12 运行，101套通过、1套失败，exit 1。唯一失败在 test_skill_content 内：预注册计划版本仍为 v11.3.12，而 manifest 已为 v11.3.13。独立读取全部原始输出，校验 receipt 记录的 SHA256，原字节保存在 `raw/regression-r2/`。

协调者随后只修订 `tests/fixtures/skill_method_ab_prereg.json`，将计划版本移到 v11.3.13，并新增 v11.3.12/基线0973/零 model_runs 的未执行历史。独立结构比较证明：还原该版本并移除新增历史后，JSON 与旧版完整相等；source_sha=null、results=[]、not-measured、作者已见 holdout 限制和所有案例/预算均保留。仓库引用检索只发现该原测试及说明文档的直接消费点。

协调者实际重跑整个失败 suite，**204/204 PASS**，exit 0；本审查核对原始回执与最终 fixture SHA，并保留原始 stdout/stderr。包装子审查者另外独立执行原失败单项，1/1 PASS。最终目标相对完整 r2 受测树的**唯一字节变化就是这个 fixture**，其余源码、测试、合同完全相同。

据此，源码 Quality 采用已通过的101套结果与完整失败suite的修复复验，属于有明确字节边界的证据复用。**没有新的本地完整102套PASS，也没有声称 exact-SHA PR/main CI 已完成。** 精确 CI 仍需真实通过后，协调者才能推进受保护发布链。相关证据：`raw/regression-r2.result.json`、`raw/prereg-repair-result.json`、`raw/source-final-bindings.json`、`packaging/raw/prereg-specific-test.json`。

## Spec 审查

| 验收 | 实质核对与结论 |
|---|---|
| 1 单测适用域 | 单一 Skill frontmatter 的 optional implicit_context 经 canonical kernel/validator 消费，没有第二份 Python/Rust 黑名单或平行路由。直接路由、trigger fallback、primary promotion 与 secondary 路径均检查适用域。缺字段保持原兼容行为，坏字段拒绝。通用非嵌入式单测拒绝，MCU/RTOS、嵌入式 Python host 和 Rust 合法路径保留；显式诊断选择不提升 mutation_permission，原 Fit/Target Gate 保留。 |
| 2 perf | cache-misses 不再固定解释成 LLC miss；LLC 主张需核对目标 CPU/PMU/kernel 的事件映射，未知/不支持写 unavailable。有效负载、等价 A/B、噪声与 no-gain/inconclusive 边界保留。 |
| 3 artifact | Root 专属 helper 与 runtime-boundary 仅适用于真实 Root 接入；独立消费者使用其已核验项目门禁。实际 claude-code/opencode team-core compiler 导出包含正确 reference，且不附带 Root helper；缺适用门禁仍阻断。 |
| 4 组合扫描 | 实际递归 rg 限定 SKILL.md，路径集合与 manifest 的65入口全等，包括9个optional及两个嵌套项。未引入新的目录权威。 |
| 5 growth | metadata、Workflow和参考条款一致：仅长期 prompt/Skill/Workflow/AGENTS/记忆晋级进入 trace-feedback-eval-handoff。普通已授权工程改进无需额外晋级；报告只读、长期候选owner review与原任务授权保留。 |
| 6 URL | 实际连接、retry、fallback绑定已核地址；每次redirect重核；Host/SNI/证书仍用原hostname。无法安全核验即停止，没有新增客户端或扩大抓取权限。 |
| 7 UBI/UBIFS | 几何核验按实际采用UBI/UBIFS才适用，覆盖PEB、min-I/O/subpage、VID/data offset、LEB、volume alignment/capacity；未知/不匹配留在host。operator、备份恢复、readback/boot与扩批独立授权完整保留。 |
| 8 多人试点 | wall-clock为经过时间，human-active为人员活跃区间并集，合计人时单列；[0,15]与[5,20]对应20并集分钟/30人分钟，单人无需多人专用字段。 |
| 9 成功路径和体积 | R-01原成功路径已恢复；新增负控没有扩大权限。原8个Profile阈值与计量器逐字未改，全部通过；9个方法源文件相对基线净-69 bytes。 |
| 10 生命周期 | 本报告完成独立source审核及限定回归证据判定；exact CI、不可变发布、Root source-only接入尚未裁决完成，runtime/product资格不继承。 |

storage与production压缩逐段对照了原文，未丢失操作授权、handoff项、六类现场证据、隐私、OTA/rollback、禁止直接设备写命令等核心要求。没有新增Skill、Agent、客户端、预算限制或全局门禁。版本包装7个投影保持一致；Manifest/TOML除版本外结构不变，M5只更新campaign身份，catalog只改unit一行并可由canonical renderer完整重建。CHANGELOG仍是Unreleased源变更说明。

## Quality 发现与关闭

| ID / 严重级别 | 初始实证 | 修复及最终处置 |
|---|---|---|
| Q-01 / Low | 初始growth测试只要求出现“普通”，隔离把正文反改为普通建议也必须晋级后仍GREEN；当前实际正文原本正确。 | 加强原测试的正文豁免及AGENTS/记忆范围。独立当前正控GREEN、5个坏变体全部RED且0errors。**已关闭**。 |
| R-01 / P2 Medium | 3f80将所有行内引号/代码内容清空，4个合法MCU/RTOS/embedded/Zephyr请求误拒；相同4例在基线全成功，而24个测试仍绿。 | 保留普通成对格式内容，只排除code fence和有限明确示例/引文标记。独立4例恢复、22邻近正反混合用例全符合预期且deny权限，fresh方法+路由25测试PASS。**已关闭**。 |
| P-01 / Low | 完整r2因未执行预注册计划版本过期导致required suite失败。 | 最小更新计划版本并保留零run历史；204项修复suite与独立原失败单项通过，JSON其他结构不变。**源码缺陷已关闭；原完整运行仍FAIL**。 |

R-01说明本审查没有用测试绿替代语义审查。当前kernel使用的是有界词法筛选，文档明确有限支持；它无法证明理解所有多语言或无关肯定背景。已有Skill Fit/Target Gate仍是执行前边界。

## 实际验证与证据区分

| 执行者与检查 | 实际结果 | 证据 |
|---|---|---|
| 独立reviewer，方法+路由fresh unittest | 25 tests PASS | raw/routing-r2-tests.* |
| 独立reviewer，额外路由正反/混合邻域 | 22/22，所有mutation_permission=deny | raw/routing-r2-neighbors.result.json |
| 独立reviewer，旧版正控 | R-01的4例在基线4/4成功 | raw/routing-baseline-success.json |
| 独立reviewer，新方法测试对旧资产 | 4 tests / 5预期assertion failures / 0errors | raw/method-controls.result.json |
| 独立reviewer，growth反例 | 当前1正控成功，5坏变体全部拒绝 | raw/growth-revised-controls.json |
| 独立reviewer，原相关质量/体积测试 | 19 tests PASS，含8原ratchets | raw/method-regressions.* |
| 独立reviewer，最终8profile计量 | 8/8 PASS，阈值与meter未改 | raw/final-ratchet.result.json |
| 独立子reviewer，包装/目录 | version identity、真实catalog生成及结构/字节比较PASS | packaging/review.md与raw/ |
| 协调者，最后一次完整回归 | 102 suites，101 PASS / 1 FAIL，exit1 | raw/regression-r2/ |
| 协调者，完整失败suite修复复验 | 204/204 PASS，exit0 | raw/prereg-repair-result.json |
| 独立子reviewer，原失败单项 | 1/1 PASS | packaging/raw/prereg-specific-test.* |

所有命令有实际argv、开始/结束时间、退出码、stdout/stderr摘要。审查过程自身的检索失败、日志索引修复、预期RED和真实产品回归均保留在negative-results.md及原始日志；没有用成功重跑覆盖旧失败。完整原始补丁位于raw/source-final.patch，hash绑定到本报告目标。

## 未测量与不授予的资格

没有native discovery/load/trigger、真实模型A/B、provider Token/费用/时延收益、真实PMU、UBI刷写、DNS客户端或现场试点测量。源字节、确定性路由、rg扫描、编译导出与一次局部续行观察不证明模型任务效果或生产率。引用的历史官方资料未在本轮重新访问互联网；本报告不把它们冒充本轮设备证据。

不新建或刷新全局Harness readiness审批，历史记录保持原范围。没有执行远端权限/分支保护的独立实时检查，也未做merge、release或Root接入。本报告不预批随后证据包装、任务状态或源文件变化；这些变化需要按实际diff复核。下列摘要绑定的是已读文件，其他未变Skill和历史证据没有被逐项重新审查。

## 原8项体积阈值

数值为source bytes，不是实际runtime context或provider Token。

| Profile | entry实际 / 原阈值 | full-source实际 / 原阈值 |
|---|---:|---:|
| core | 97817 / 133940 | 172867 / 184133 |
| embedded-fullstack | 209914 / 245296 | 316262 / 316854 |
| incident-response | 30434 / 37797 | 46534 / 46612 |
| large-refactor | 212939 / 248328 | 323144 / 323328 |
| personal-core | 112851 / 152918 | 191638 / 204293 |
| release-hardening | 82373 / 112256 | 156243 / 159576 |
| research-intake | 65344 / 86571 | 117004 / 124543 |
| team-core | 123385 / 166442 | 210831 / 223333 |

## 被审文件 SHA256

完整机器记录还包含每个文件的字节数、冻结对象一致性和review owner。

| 文件 | SHA256 |
|---|---|
| `.version-lock` | `568734e9c06433abc958919a68b3ddab5c84f72c875175e874bdd19ea3da640d` |
| `CHANGELOG.md` | `c606936f71eedf938b847bc169e5cefc9d3c56b7884ea4b7f83b6d2f46a1450d` |
| `CONTEXT.md` | `a426e5463488a1107e43483c6cb1ccd35b4313ce6ccc46eecdf84cea11c1f91a` |
| `README.md` | `38f647d6648ad5e6aeba9464c89ad5c71b49ef6b63dccb0328b8476d4b116b78` |
| `docs/agent-skill-catalog.md` | `6804c7a0f8424898912c6b8daf03128d235d5945081b987e99a40a2269b94fa6` |
| `docs/changes/20261117-skill-scope-methods/design.md` | `06aae095e7ea200dffe9051d7cadae46b9f922e1551e43d98aa4dc17ffeeb147` |
| `docs/changes/20261117-skill-scope-methods/requirements.md` | `987f00a4cc1deee41ca302195648452fc354ad96d2f47f0a9aa060c70ce55098` |
| `docs/changes/20261117-skill-scope-methods/tasks.md` | `0bdeae2656bca57ba008eee2ae1d40f4e39d252f1dea6a73cd2d552c4f7a5c49` |
| `docs/commands.md` | `07e722cc8d90c06d006ef3ef9e880b1c911fc1ab00a956ae0bd7f47465e18c28` |
| `manifest.json` | `07e887a7417f81ea279a107981aa0fd25836aa85d140f26734d78733c0e0ce68` |
| `manifests/software_m5_eval_contract.json` | `92f186adf1d906b84e6925ff1001a9b353ebbedb784744669c21db3d6f0037ce` |
| `optional-skills/adk-data-fetch/adk-fetch-url-content/SKILL.md` | `21e9223a92ec6f50b336fc9bb8cd041f7db533cbfc216350c64a0b748ce2328a` |
| `optional-skills/adk-skill-composition-governance/SKILL.md` | `062d145077d6d56ad0d038cf8d3de62f3368bc3f1c561660aa209830dcaa38f6` |
| `pyproject.toml` | `18c4ea37d322fe5453019a1e674a27d22ede1741e3f8ebf01d0c019183de4a54` |
| `skills/adk-artifact-gating/SKILL.md` | `17f658a180bb848f98a0ffa91831e82fc980d7fcdae78782c103fb4862f5fa4e` |
| `skills/adk-artifact-gating/references/details.md` | `c4f1f8675a02c8e3886417b48caa6c1ba2dad15fd5246dfb02e1ae6980b42f3f` |
| `skills/adk-embedded-storage-layout-migration/SKILL.md` | `60689906562d9146431960b421c1d2731090f5377c1cd5923adb13ab589b7c27` |
| `skills/adk-engineering-growth-review/SKILL.md` | `551c03d625fb6d884f03e112d49d9d39eee8d50a628009a93b5cf67ab051b5b8` |
| `skills/adk-performance-profiling-embedded/SKILL.md` | `429e8f4bdab43522b6deb89ad98cf20f30c7a8b8f80be2810e6511ca62149000` |
| `skills/adk-production-field-readiness/SKILL.md` | `b661f56a96309870e2895423ee3646bd9e50a5f35da9286cd070a45ac75a60e6` |
| `skills/adk-production-field-readiness/references/pilot-measurement-evidence.md` | `33e1ecdae9f7baed2e7a050bc718e716200d76934489419f2d7be5c4b3776a62` |
| `skills/adk-unit-test-embedded/SKILL.md` | `a17d781e18dc5f72d6485f1ca8f5a9e6f6612ddeb761340110083b35181ffbe9` |
| `src/agent_dev_kit/__init__.py` | `2e6f4cf157d25085a13582c7aaa16d5ddaae5ac8aca72a41c04c9d2fbaf0a1b8` |
| `src/agent_dev_kit/_matcher_kernel.py` | `a573041b767280f3c390a563308ec580c51d6e7c92427099681e46b2f850a58d` |
| `src/agent_dev_kit/matcher.py` | `27d9519150922ceaf7a65f196bbdadb3c8915834becd41cf13cd1c8914ed7209` |
| `src/agent_dev_kit/validation_contract.py` | `055051177bda58f8a2558afe654fbf7117b1b4334730f4c296c10cf9c21e03ab` |
| `tests/fixtures/skill_method_ab_prereg.json` | `ff535f0c999111ab50c2a4ba8ce0daa5de2c17bd3691d2007d010c438456aeb5` |
| `tests/test_boundary_conditions_match.sh` | `22d364ecdb59bbae8108be0ef829cde302ec25400381e062bcbc1661f3c34ea8` |
| `tests/test_match_effectiveness.sh` | `db3a0e902f9addeab80d9a48d953b9f8b49f0919807f423b96b50bf20e3b0af2` |
| `tests/test_skill_content.sh` | `d10d6b5e7a79811d2a8ef87439c81bd3db22e5284ccc0602c54e4a8af6a14f5d` |
| `tests/test_skill_scope_methods.py` | `bb6aefafed45d77f482b39046ab933c414c2365f1f3568adc1f66d0444964f62` |
| `tests/test_skill_trigger_matrix.py` | `2b6d67cc774b25a817141b370cdadd6c3661d13e3ef35500e8a5767ce3131d64` |

策略文件及其SHA见JSON的policy_sources；关键证据原始文件SHA见evidence。以上源级结论以此exact target为边界。
