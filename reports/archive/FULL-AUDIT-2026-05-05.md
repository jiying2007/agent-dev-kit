     1|     1|     1|     1|     1|     1|# agent-dev-kit v2.0.0 全量深度审计报告
     2|     2|     2|     2|     2|     2|
     3|     3|     3|     3|     3|     3|> 审计时间: 2026-05-05
     4|     4|     4|     4|     4|     4|> 审计方式: 逐层真实执行验证，非文档审查
     5|     5|     5|     5|     5|     5|> 审计范围: 全部 scripts/skills/agents/profiles/templates/tests/docs 交叉依赖
     6|     6|     6|     6|     6|     6|> 审计结论: **框架骨架优秀，但存在 5 个阻断级 + 8 个高优问题，不满足"研发团队拿来即用"**
     7|     7|     7|     7|     7|     7|
     8|     8|     8|     8|     8|     8|---
     9|     9|     9|     9|     9|     9|
    10|    10|    10|    10|    10|    10|## 一、全局统计
    11|    11|    11|    11|    11|    11|
    12|    12|    12|    12|    12|    12|| 维度 | 数量 |
    13|    13|    13|    13|    13|    13||------|------|
    14|    14|    14|    14|    14|    14|| 总文件数 | 666（含 .git） |
    15|    15|    15|    15|    15|    15|| 有效文件数 | ~130（排除 .git） |
    16|    16|    16|    16|    16|    16|| Core Agents | 10 |
    17|    17|    17|    17|    17|    17|| Core Skills | 28 |
    18|    18|    18|    18|    18|    18|| Optional Skills | 9 |
    19|    19|    19|    19|    19|    19|| Profiles | 10 |
    20|    20|    20|    20|    20|    20|| Templates | 18（顶层 7 + artifacts 8 + workflows 2 + agent/skill 模板） |
    21|    21|    21|    21|    21|    21|| Tests | 25 |
    22|    22|    22|    22|    22|    22|| Scripts | 24 |
    23|    23|    23|    23|    23|    23|| Docs | 42+（含 26 runbooks） |
    24|    24|    24|    24|    24|    24|| 总代码行数（scripts） | 5,806 |
    25|    25|    25|    25|    25|    25|
    26|    26|    26|    26|    26|    26|---
    27|    27|    27|    27|    27|    27|
    28|    28|    28|    28|    28|    28|## 二、版本一致性审计
    29|    29|    29|    29|    29|    29|
    30|    30|    30|    30|    30|    30|| 位置 | 版本值 | 状态 |
    31|    31|    31|    31|    31|    31||------|--------|------|
    32|    32|    32|    32|    32|    32|| manifest.yaml | 2.0.0 | ✅ 正确 |
    33|    33|    33|    33|    33|    33|| README.md | 2.0.0 | ✅ 正确 |
    34|    34|    34|    34|    34|    34|| CHANGELOG.md | 2.0.0 | ✅ 正确 |
    35|    35|    35|    35|    35|    35|| .version-lock | 1.0.0 | ❌ **未同步更新** |
    36|    36|    36|    36|    36|    36|| commands.md | 0.3.0 | ❌ **过期** |
    37|    37|    37|    37|    37|    37|| usage.md | 0.3.0 | ❌ **过期** |
    38|    38|    38|    38|    38|    38|| FINAL-RELEASE.md | 1.0.0 | ❌ **过期** |
    39|    39|    39|    39|    39|    39|| RELEASE-1.0.0.md | 1.0.0 | ❌ **过期** |
    40|    40|    40|    40|    40|    40|
    41|    41|    41|    41|    41|    41|**问题**: 版本号在 6 个文件中不一致。`.version-lock` 是锁定文件却停留在 1.0.0。
    42|    42|    42|    42|    42|    42|
    43|    43|    43|    43|    43|---
    44|    44|    44|    44|    44|
    45|    45|    45|    45|    45|## 三、manifest.yaml 结构审计
    46|    46|    46|    46|    46|
    47|    47|    47|    47|    47|### 3.1 版本与配置矛盾
    48|    48|    48|    48|    48|
    49|    49|    49|    49|    49|| 字段 | 值 | 问题 |
    50|    50|    50|    50|    50||------|------|------|
    51|    51|    51|    51|    51|| install.default_mode | copy | OK |
    52|    52|    52|    52|    52|| install.command | --mode symlink | 与 default_mode 矛盾 |
    53|    53|    53|    53|    53|
    54|    54|    54|    54|    54|问题: install.default_mode 设为 copy，但 install.command 示例用 --mode symlink。新用户按文档操作会覆盖默认行为。
    55|    55|    55|    55|    55|
    56|    56|    56|    56|    56|### 3.2 Agents 声明完整性
    57|    57|    57|    57|    57|
    58|    58|    58|    58|    58|10/10 Agent 声明与文件一一对应，无缺失。
    59|    59|    59|    59|    59|
    60|    60|    60|    60|    60|### 3.3 Skills 声明完整性
    61|    61|    61|    61|    61|
    62|    62|    62|    62|    62|| 类型 | manifest 声明数 | 文件存在数 | 缺失 |
    63|    63|    63|    63|    63||------|---------------|-----------|------|
    64|    64|    64|    64|    64|| Core Skills | 28 | 28 | 0 |
    65|    65|    65|    65|    65|| Optional Skills | 9 | 9 | 0 |
    66|    66|    66|    66|    66|
    67|    67|    67|    67|    67|37/37 Skill 声明与文件一一对应，无缺失。
    68|    68|    68|    68|    68|
    69|    69|    69|    69|    69|### 3.4 Profile 完整性
    70|    70|    70|    70|    70|
    71|    71|    71|    71|    71|| Profile | extends | optional | conflicts_with | trigger_examples |
    72|    72|    72|    72|    72||---------|---------|----------|---------------|-----------------|
    73|    73|    73|    73|    73|| core | - | - | - | 3条 OK |
    74|    74|    74|    74|    74|| personal-core | core | - | - | 3条 OK |
    75|    75|    75|    75|    75|| embedded-fullstack | core | - | - | 3条 OK |
    76|    76|    76|    76|    76|| release-hardening | - | yes | incident-response | 3条 OK |
    77|    77|    77|    77|    77|| adk-artifact-gated-lite | core | yes | - | 无 缺失 |
    78|    78|    78|    78|    78|| team-core | core | yes | - | 3条 OK |
    79|    79|    79|    79|    79|| openspec-driven | core | yes | - | 3条 OK |
    80|    80|    80|    80|    80|| large-refactor | core | yes | release-hardening | 3条 OK |
    81|    81|    81|    81|    81|| incident-response | core | yes | release-hardening | 3条 OK |
    82|    82|    82|    82|    82|| research-intake | - | yes | - | 3条 OK |
    83|    83|    83|    83|    83|
    84|    84|    84|    84|    84|发现:
    85|    85|    85|    85|    85|- adk-artifact-gated-lite 缺少 trigger_examples
    86|    86|    86|    86|    86|- 冲突不对称: large-refactor 声明 conflicts_with release-hardening，但 release-hardening 未声明 conflicts_with large-refactor
    87|    87|    87|    87|    87|
    88|    88|    88|    88|    88|### 3.5 Routing 表
    89|    89|    89|    89|    89|
    90|    90|    90|    90|    90|- 21 条路由条目，覆盖全部 28 个 core skills 中的 21 个
    91|    91|    91|    91|    91|- 7 个 skill 未被 routing 覆盖: adk-adr-writer, adk-bsp-porting-playbook, adk-rtos-task-design, adk-interrupt-dma-patterns, adk-protocol-stack-integration, adk-component-api-stability, adk-cmake-cross-build
    92|    92|    92|    92|    92|- routing 表未被 skill_match.sh 消费（详见 Scripts 层审计）
    93|    93|    93|    93|    93|
    94|    94|    94|    94|---
    95|    95|    95|    95|
    96|    96|    96|    96|## 四、Scripts 层审计（24 个脚本）
    97|    97|    97|    97|
    98|    98|    98|    98|### 4.1 总览
    99|    99|    99|    99|
   100|   100|   100|   100|| 指标 | 值 |
   101|   101|   101|   101||------|------|
   102|   102|   102|   102|| 总脚本数 | 24 |
   103|   103|   103|   103|| 总代码行 | 5,806 |
   104|   104|   104|   104|| bash -n 语法检查 | 24/24 通过 |
   105|   105|   105|   105|| 有 set -euo pipefail | 23/24（lib_manifest.sh 缺失） |
   106|   106|   106|   106|| 有 usage 函数 | 22/24 |
   107|   107|   107|   107|| 通过 devkit.sh 路由 | 8/24 |
   108|   108|   108|   108|
   109|   109|   109|   109|### 4.2 功能分层
   110|   110|   110|   110|
   111|   111|   111|   111|核心管线（通过 devkit.sh 路由，8 个）:
   112|   112|   112|   112|- devkit.sh .............. 路由分发器
   113|   113|   113|   113|- install_assets.sh ...... 安装 agents/skills 到工具目录
   114|   114|   114|   114|- validate_assets.sh ..... 校验 manifest 结构/Schema
   115|   115|   115|   115|- convert_assets.sh ...... 导出到其他工具格式
   116|   116|   116|   116|- catalog_assets.sh ...... 构建/搜索目录索引
   117|   117|   117|   117|- skill_match.sh ......... 文本匹配 skill triggers
   118|   118|   118|   118|- openspec_bridge.sh ..... OpenSpec 变更导入导出
   119|   119|   119|   119|- evidence_index.sh ...... 追加证据到 markdown 表格
   120|   120|   120|   120|- workflow.sh ............ 变更生命周期（propose/apply/verify/review/archive）
   121|   121|   121|   121|
   122|   122|   122|   122|库文件（1 个）:
   123|   123|   123|   123|- lib_manifest.sh ........ YAML manifest 解析库
   124|   124|   124|   124|
   125|   125|   125|   125|质量门禁（未路由，2 个）:
   126|   126|   126|   126|- quality-gate-check.sh .. 检查工件/一致性/证据/profiles
   127|   127|   127|   127|- enhanced-gate-check.sh . 与 quality-gate-check.sh 完全相同（死代码）
   128|   128|   128|   128|
   129|   129|   129|   129|内部调用（被其他脚本调用，3 个）:
   130|   130|   130|   130|- check_change_governance.sh .. 校验变更工件结构
   131|   131|   131|   131|- check_format.sh ............. 检查 CRLF/tabs/shebangs
   132|   132|   132|   132|- check_profile_coherence.sh .. 校验 profile 继承
   133|   133|   133|   133|
   134|   134|   134|   134|运维/生产（未路由，8 个）:
   135|   135|   135|   135|- health-check.sh ........ 结构/依赖/配置/测试/质量检查
   136|   136|   136|   136|- backup-rollback.sh ..... 备份/恢复/列表/回滚/验证
   137|   137|   137|   137|- auto-ops.sh ............ 日常/周常/月常运维编排
   138|   138|   138|   138|- monitoring.sh .......... 系统监控/告警/报告
   139|   139|   139|   139|- performance.sh ......... 性能分析/优化/基准测试
   140|   140|   140|   140|- security.sh ............ 安全扫描/加固/审计/报告
   141|   141|   141|   141|- release-manager.sh ..... 发布准备/验证/构建/发布/回滚
   142|   142|   142|   142|- version-manager.sh ..... 版本查看/锁定/解锁/升级/对比
   143|   143|   143|   143|
   144|   144|   144|   144|无用包装（1 个）:
   145|   145|   145|   145|- sync_codex_assets.sh ... 仅 5 行，调用 install_assets.sh --tool codex
   146|   146|   146|   146|
   147|   147|   147|   147|### 4.3 阻断级问题
   148|   148|   148|   148|
   149|   149|   149|   149|#### 阻断-S1: quality-gate-check.sh 与 enhanced-gate-check.sh 完全重复
   150|   150|   150|   150|
   151|   151|   151|   151|两文件均为 389 行、9976 字节，MD5 完全相同: 5f6b8b7fa5b734ee243310b838c17511
   152|   152|   152|   152|
   153|   153|   153|   153|其中一个完全是死代码。
   154|   154|   154|   154|
   155|   155|   155|   155|#### 阻断-S2: match 功能 0/7 命中率
   156|   156|   156|   156|
   157|   157|   157|   157|skill_match.sh 读取 SKILL.md 的 triggers 字段做子串匹配。
   158|   158|   158|   158|但 triggers 写的是描述性句子（"收到模糊需求或跨团队需求时"），不是可匹配关键词。
   159|   159|   159|   159|routing 表（21 条 intent_zh）存在但 match 脚本完全不读取。
   160|   160|   160|   160|
   161|   161|   161|   161|测试结果:
   162|   162|   162|   162|- "需要澄清需求"    -> adk-requirements-triage:    FAIL
   163|   163|   163|   163|- "拆解这个任务"    -> adk-task-breakdown:         FAIL
   164|   164|   164|   164|- "写单元测试"      -> adk-unit-test-embedded:     FAIL
   165|   165|   165|   165|- "调试这个问题"    -> adk-systematic-debugging:   FAIL
   166|   166|   166|   166|- "准备提交代码"    -> adk-commit-pr-quality-gate:  FAIL
   167|   167|   167|   167|- "设计寄存器映射"  -> adk-register-map-design:    FAIL
   168|   168|   168|   168|- "我要写驱动"      -> adk-driver-bringup-checklist: FAIL
   169|   169|   169|   169|
   170|   170|   170|   170|### 4.4 高优问题
   171|   171|   171|   171|
   172|   172|   172|   172|#### 高优-S1: 13 个脚本未通过 devkit.sh 路由
   173|   173|   173|   173|
   174|   174|   174|   174|auto-ops.sh, backup-rollback.sh, check_change_governance.sh, check_format.sh,
   175|   175|   175|   175|check_profile_coherence.sh, enhanced-gate-check.sh, health-check.sh,
   176|   176|   176|   176|monitoring.sh, performance.sh, quality-gate-check.sh, release-manager.sh,
   177|   177|   177|   177|security.sh, version-manager.sh
   178|   178|   178|   178|
   179|   179|   179|   179|运维脚本（health-check, backup-rollback, auto-ops, monitoring, performance, security, release-manager, version-manager）用户无法通过 devkit.sh 发现。
   180|   180|   180|   180|
   181|   181|   181|   181|#### 高优-S2: 跨脚本重复函数
   182|   182|   182|   182|
   183|   183|   183|   183|- to_lower(): catalog_assets.sh:100 和 skill_match.sh:54 完全相同
   184|   184|   184|   184|- resolve_profile_items(): install_assets.sh:169 和 convert_assets.sh:93 完全相同
   185|   185|   185|   185|- run_cmd(): install_assets.sh:123 和 convert_assets.sh:85 完全相同
   186|   186|   186|   186|- frontmatter 解析: catalog_assets.sh:68 和 skill_match.sh:64 逻辑相似但函数名不同
   187|   187|   187|   187|
   188|   188|   188|   188|应统一收入 lib_manifest.sh。
   189|   189|   189|   189|
   190|   190|   190|   190|#### 高优-S3: 4 个脚本依赖 rg（ripgrep）但未检查
   191|   191|   191|   191|
   192|   192|   192|   192|check_change_governance.sh, check_format.sh, openspec_bridge.sh, workflow.sh 使用 rg 但未检查是否安装。
   193|   193|   193|   193|
   194|   194|   194|   194|health-check.sh 检查 bash/git/tar/grep/sed/awk 但不检查 ripgrep。
   195|   195|   195|   195|
   196|   196|   196|   196|#### 高优-S4: 2 个脚本有交互式 read -p
   197|   197|   197|   197|
   198|   198|   198|   198|backup-rollback.sh:70 和 release-manager.sh:61 使用 read -p 会在 CI/非交互环境挂起。
   199|   199|   199|   199|
   200|   200|   200|   200|#### 高优-S5: performance.sh optimize 会破坏 .md 文件
   201|   201|   201|   201|
   202|   202|   202|   202|performance.sh:107 执行 sed -i 删除 .md 文件所有空行，破坏 markdown 渲染。
   203|   203|   203|   203|
   204|   204|   204|   204|auto-ops.sh:215 对 .md 文件执行 gzip -k，产生无用 .gz 文件。
   205|   205|   205|   205|
   206|   206|   206|   206|#### 高优-S6: lib_manifest.sh 缺少 set -euo pipefail
   207|   207|   207|   207|
   208|   208|   208|   208|作为库文件被 6 个脚本 source，自身无错误处理保护。
   209|   209|   209|   209|
   210|   210|   210|   210|#### 高优-S7: auto-ops.sh 解析 --force 但从未使用
   211|   211|   211|   211|
   212|   212|   212|   212|变量 force 被解析存储但无任何函数引用，属于死代码。
   213|   213|   213|   213|
   214|   214|   214|   214|#### 高优-S8: monitoring.sh start 进入无限循环
   215|   215|   215|   215|
   216|   216|   216|   216|start_monitoring() 进入 while true 死循环，无后台守护机制。
   217|   217|   217|   217|
   218|   218|   218|---
   219|   219|   219|
   220|   220|   220|## 五、Skills 层审计（28 Core + 9 Optional = 37 个）
   221|   221|   221|
   222|   222|   222|### 5.1 总览
   223|   223|   223|
   224|   224|   224|| 指标 | 值 |
   225|   225|   225||------|------|
   226|   226|   226|| 总 Skill 数 | 37（28 core + 9 optional） |
   227|   227|   227|| Frontmatter 完整 | 27/37（73%） |
   228|   228|   228|| Body 结构完整 | 37/37（100%） |
   229|   229|   229|| p0 anti-rationalization | 10/10（100%） |
   230|   230|   230|| 可匹配 triggers | 8/37（22%） |
   231|   231|   231|| 描述性 triggers | 29/37（78%） |
   232|   232|   232|
   233|   233|   233|### 5.2 Frontmatter 完整性
   234|   234|   234|
   235|   235|   235|缺失 version + last_updated 的 10 个 skill:
   236|   236|   236|- adk-grill-with-docs, adk-diagnose-loop, adk-code-simplification, adk-context-engineering
   237|   237|   237|- adk-chinese-commit-conventions, adk-chinese-code-review
   238|   238|   238|- adk-fetch-url-content, adk-email-imap-fetch
   239|   239|   239|
   240|   240|   240|其余 27 个均具备 name/description/version/last_updated/triggers/non_triggers/inputs/outputs/constraints 共 9 个字段。
   241|   241|   241|
   242|   242|   242|### 5.3 Trigger 质量分类
   243|   243|   243|
   244|   244|   244|可匹配（关键词式，8 个）:
   245|   245|   245|- adk-grill-with-docs: "需求不清楚"
   246|   246|   246|- adk-diagnose-loop: "诊断循环"
   247|   247|   247|- adk-code-simplification: "代码简化"
   248|   248|   248|- adk-context-engineering: "上下文工程"
   249|   249|   249|- adk-chinese-commit-conventions: "中文提交"
   250|   250|   250|- adk-chinese-code-review: "中文评审"
   251|   251|   251|- adk-fetch-url-content: "抓取网页"
   252|   252|   252|- adk-email-imap-fetch: "获取邮件"
   253|   253|   253|
   254|   254|   254|不可匹配（描述性句子，29 个）:
   255|   255|   255|- "收到模糊需求或跨团队需求时"（adk-requirements-triage）
   256|   256|   256|- "任务过大或多人协作时"（adk-task-breakdown）
   257|   257|   257|- "准备声明完成并发起PR前"（adk-verification-before-completion）
   258|   258|   258|- "准备 commit/PR 或代码评审前"（adk-commit-pr-quality-gate）
   259|   259|   259|- ...其余 25 个类似
   260|   260|   260|
   261|   261|   261|核心矛盾: 两种 trigger 风格并存，匹配引擎只能处理一种。
   262|   262|   262|
   263|   263|   263|### 5.4 内容重叠
   264|   264|   264|
   265|   265|   265|| Skill A | Skill B | 重叠程度 | 说明 |
   266|   266|   266||---------|---------|---------|------|
   267|   267|   267|| adk-systematic-debugging | adk-diagnose-loop | 高 | 都是调试定位流程 |
   268|   268|   268|| adk-verification-before-completion | adk-commit-pr-quality-gate | 中 | 都涉及提交前检查 |
   269|   269|   269|| adk-requirements-triage | adk-grill-with-docs | 中 | 都涉及需求澄清 |
   270|   270|   270|
   271|   271|   271|### 5.5 内部重复段落
   272|   272|   272|
   273|   273|   273|adk-grill-with-docs 和 adk-diagnose-loop 存在内部重复章节（核心流程 = Workflow 重复出现）。
   274|   274|   274|
   275|   275|   275|### 5.6 尾部模板不一致
   276|   276|   276|
   277|   277|   277|三种尾部模板并存:
   278|   278|   278|- 健壮性规范（22 个 skill）
   279|   279|   279|- 合理化借口拦截（14 个 skill）
   280|   280|   280|- 无尾部模板（7 个 skill）
   281|   281|   281|
   282|   282|---
   283|   283|
   284|   284|## 六、Agents 层审计（10 个）
   285|   285|
   286|   286|### 6.1 总览
   287|   287|
   288|   288|| 指标 | 值 |
   289|   289||------|------|
   290|   290|| Agent 总数 | 10 |
   291|   291|| 结构一致性 | 10/10（100%） |
   292|   292|| 职责边界清晰 | 10/10（100%） |
   293|   293|| 中文内容质量 | 优秀 |
   294|   294|
   295|   295|所有 10 个 agent 统一结构: 角色定位、适用输入、核心决策规则、执行流程、必跑验证、阻塞与升级、输出契约、场景输入样例、输出样例(pass/needs-fix)。
   296|   296|
   297|   297|### 6.2 逐个评估
   298|   298|
   299|   299|| Agent | 行数 | 决策规则数 | 职责清晰度 | 边界声明 |
   300|   300||-------|------|-----------|-----------|---------|
   301|   301|| requirements-analyst | 60 | 7 | 优秀 | 排除实现与发布 |
   302|   302|| architecture-planner | 57 | 6 | 优秀 | 排除完整实现 |
   303|   303|| driver-engineer | 50 | 3 | 优秀 | 排除应用层与发布决策 |
   304|   304|| component-engineer | 50 | 3 | 优秀 | 排除硬件 bring-up 与发布签名 |
   305|   305|| application-engineer | 53 | 4 | 优秀 | 排除硬件寄存器与发布决策 |
   306|   306|| build-release-engineer | 55 | 5 | 优秀 | 排除需求优先级排序 |
   307|   307|| test-validation-engineer | 62 | 9 | 优秀 | 排除架构决策与发布审批 |
   308|   308|| performance-reliability-engineer | 50 | 3 | 优秀 | 排除安全合规 |
   309|   309|| security-compliance-reviewer | 50 | 3 | 优秀 | 排除发布合并操作 |
   310|   310|| code-review-governor | 67 | 13 | 优秀 | 排除需求拆解 |
   311|   311|
   312|   312|### 6.3 边界冲突分析
   313|   313|
   314|   314|无硬性边界冲突。所有 agent 均有明确的"非职责范围"声明。
   315|   315|
   316|   316|互补重叠（良性）:
   317|   317|- test-validation-engineer 与 code-review-governor 都引用 Evidence Index，但前者是生产者，后者是消费者
   318|   318|- requirements-analyst 与 architecture-planner 共享 scope/boundary 概念，但是顺序关系（需求喂给架构）
   319|   319|
   320|   320|结论: Agent 层质量优秀，无需修改。
   321|   321|
   322|   322|---
   323|   323|
   324|   324|## 七、Profiles 层审计（10 个）
   325|   325|
   326|   326|### 7.1 继承链
   327|   327|
   328|   328|| Profile | extends | 继承解析 |
   329|   329||---------|---------|---------|
   330|   330|| personal-core | core | 正确 |
   331|   331|| embedded-fullstack | core | 正确 |
   332|   332|| adk-artifact-gated-lite | core | 正确 |
   333|   333|| team-core | core | 正确 |
   334|   334|| openspec-driven | core | 正确 |
   335|   335|| large-refactor | core | 正确 |
   336|   336|| incident-response | core | 正确 |
   337|   337|| release-hardening | - | 独立，正确 |
   338|   338|| research-intake | - | 独立，正确 |
   339|   339|
   340|   340|所有继承链解析正确。
   341|   341|
   342|   342|### 7.2 默认 Profile
   343|   343|
   344|   344|default_profile = embedded-fullstack
   345|   345|
   346|   346|包含: 10 agents + 22 skills。作为嵌入式开发导向仓库的默认配置，合理。
   347|   347|
   348|   348|### 7.3 Core Profile 覆盖
   349|   349|
   350|   350|core 包含 5 个通用 agent:
   351|   351|- requirements-analyst, architecture-planner, application-engineer
   352|   352|- test-validation-engineer, code-review-governor
   353|   353|
   354|   354|未包含的 5 个领域 agent（由子 profile 按需添加）:
   355|   355|- driver-engineer, component-engineer, build-release-engineer
   356|   356|- performance-reliability-engineer, security-compliance-reviewer
   357|   357|
   358|   358|设计合理。
   359|   359|
   360|   360|### 7.4 问题
   361|   361|
   362|   362|| 编号 | 严重度 | 问题 |
   363|   363||------|--------|------|
   364|   364|| P-1 | 高 | 冲突不对称: large-refactor -> release-hardening 存在，但反向缺失 |
   365|   365|| P-2 | 中 | adk-artifact-gated-lite 缺少 trigger_examples |
   366|   366|| P-3 | 低 | release-hardening 独立（不 extends core），与其他 optional profile 风格不一致 |
   367|   367|
   368|---
   369|
   370|## 八、Templates 层审计（18 个）
   371|
   372|### 8.1 顶层模板（7 个）
   373|
   374|| 模板 | 行数 | 状态 | 说明 |
   375||------|------|------|------|
   376|| agent-template.md | 31 | 完整 | 新 agent 骨架 |
   377|| skill-template.md | 35 | 完整 | 新 skill 骨架，含 frontmatter + workflow |
   378|| agent-handoff.md | 30 | 完整 | 标准化交接协议 |
   379|| quality-score.md | 60 | 完整 | 5 维度评分量表 |
   380|| ready.md | 24 | 完整 | 非阻塞交付模板 |
   381|| blocked.md | 27 | 完整 | 缺失输入阻塞模板 |
   382|| exec-plan.md | 54 | 完整 | 6 元素执行计划 + Evidence Index |
   383|
   384|### 8.2 工件模板（8 个，templates/artifacts/）
   385|
   386|| 模板 | 行数 | 状态 | 说明 |
   387||------|------|------|------|
   388|| prd-template.md | 104 | 完整 | 完整 8 段 PRD |
   389|| user-story-template.md | 27 | 完整 | 用户故事 + 验收标准 |
   390|| design-spec-template.md | 17 | 桩 | 仅占位概述 |
   391|| test-report-template.md | 17 | 桩 | 仅占位概述 |
   392|| review-report-template.md | 17 | 桩 | 仅占位概述 |
   393|| implementation-plan-template.md | 17 | 桩 | 仅占位概述 |
   394|| system-arch-template.md | 17 | 桩 | 仅占位概述 |
   395|| adk-task-breakdown-template.md | 17 | 桩 | 仅占位概述 |
   396|| approval-template.md | 17 | 桩 | 仅占位概述 |
   397|
   398|**问题: 7/8 个工件模板是桩文件（17 行，仅占位概述），无实际结构。**
   399|
   400|### 8.3 工作流模板（2 个，templates/workflows/）
   401|
   402|| 模板 | 行数 | 状态 |
   403||------|------|------|
   404|| standard-workflow-template.md | 14 | 极简，仅 5 个阶段名 |
   405|| emergency-workflow-template.md | 14 | 极简，仅 5 个阶段名 |
   406|
   407|---
   408|
   409|## 九、Tests 层审计（25 个）
   410|
   411|### 9.1 执行结果
   412|
   413|全部 25 个测试通过（timeout 15s）。
   414|
   415|| 测试 | 结果 | 说明 |
   416||------|------|------|
   417|| test_anti_rationalization.sh | PASS | 8/8 通过 |
   418|| test_asset_content_quality.sh | PASS | |
   419|| test_boundary_conditions.sh | PASS | 10/10 通过 |
   420|| test_catalog.sh | PASS | |
   421|| test_change_governance.sh | PASS | |
   422|| test_context_md.sh | PASS | 8/8 通过 |
   423|| test_convert.sh | PASS | |
   424|| test_enhanced_gate_check.sh | PASS | 4/4 通过 |
   425|| test_evidence_index.sh | PASS | |
   426|| test_format.sh | PASS | |
   427|| test_install.sh | PASS | |
   428|| test_integration.sh | PASS | 5 个测试全通过 |
   429|| test_no_external_repo_refs.sh | PASS | |
   430|| test_openspec_bridge.sh | PASS | |
   431|| test_optional_skills.sh | PASS | |
   432|| test_profile_coherence_enhanced.sh | PASS | 5/5 通过 |
   433|| test_profile_coherence.sh | PASS | 有冲突警告 |
   434|| test_profile_conflicts.sh | PASS | 有冲突警告 |
   435|| test_routing.sh | PASS | 21 条路由验证 |
   436|| test_skill_dependencies.sh | PASS | 28 个依赖验证 |
   437|| test_skill_trigger_matrix.sh | PASS | |
   438|| test_templates.sh | PASS | 14/14 通过 |
   439|| test_validate.sh | PASS | strict + quick |
   440|| test_workflow.sh | PASS | 需要约 12s |
   441|| run_all.sh | PASS | 全量回归 |
   442|
   443|### 9.2 测试质量问题
   444|
   445|| 编号 | 问题 | 严重度 |
   446||------|------|--------|
   447|| T-1 | test_workflow.sh 需要 12s，默认 10s timeout 会误报 FAIL | 中 |
   448|| T-2 | routing 测试只验证字段存在，不验证 match 功能可用 | 高 |
   449|| T-3 | 测试全 PASS 但 match 功能 0/7 命中率未被发现 | 高 |
   450|
   451|核心矛盾: 测试套件报告全绿，但核心功能（意图路由）完全不工作。
   452|
---

## 十、Docs 层审计

### 10.1 NAVIGATION.md 引用检查

| 引用文件 | 存在 | 状态 |
|---------|------|------|
| quick-start.md | 是 | OK |
| usage.md | 是 | OK |
| commands.md | 是 | OK |
| troubleshooting.md | 是 | OK |
| best-practices.md | 是 | OK |
| CONTRIBUTING.md | 是 | OK |
| codex-agents-integration.md | 是 | OK |
| skill-composition-guide.md | 是 | OK |
| mapping-matrix.md | 是 | OK |
| reference-adoption.md | 是 | OK |
| workflows.md | 是 | OK |
| agent-skill-catalog.md | 是 | OK |
| skill-dependency-graph.md | 是 | OK |
| skill-routing.md | 否 | 缺失 |
| CHANGELOG.md | 是 | OK |

### 10.2 文档版本过期

| 文件 | 引用版本 | 实际版本 | 状态 |
|------|---------|---------|------|
| commands.md | 0.3.0 | 2.0.0 | 过期 |
| usage.md | 0.3.0 | 2.0.0 | 过期 |
| FINAL-RELEASE.md | 1.0.0 | 2.0.0 | 过期 |
| RELEASE-1.0.0.md | 1.0.0 | 2.0.0 | 过期 |

### 10.3 文档引用缺失脚本

commands.md 和 usage.md 引用了不属于本仓库的脚本:
- scripts/check-global-codex-health.sh（在父仓库 llm_agent 中）
- scripts/check-adk-harden-readiness.sh（在父仓库 llm_agent 中）

这些是跨仓库引用，未标注说明，会让新用户困惑。

### 10.4 测试产物残留

docs/changes/archive/20260505-test-e2e-001/ 是之前审计时的测试产物，应清理。

---

## 十一、框架变形诊断

### 11.1 结构是否变形

结论: **轻度变形，未失控。**

变形表现:
1. Scripts 层膨胀: 24 个脚本中 8 个运维脚本（health/backup/monitoring/performance/security/release/version/auto-ops）与核心管线职责不同，但放在同一目录
2. 两种 trigger 风格并存: 29 个描述性 vs 8 个关键词式，设计不统一
3. 工件模板 7/8 是桩文件，表明"先搭结构再填充"的工作流未完成
4. enhanced-gate-check.sh 完全重复，表明增量开发中缺乏去重检查

未失控表现:
1. 核心管线（devkit.sh -> install/validate/convert/catalog/match/workflow）职责清晰
2. Agent 层零冲突
3. Profile 继承链全部正确
4. 测试覆盖全面（25 个测试全通过）

### 11.2 代码文档结构合理性

| 维度 | 评价 | 说明 |
|------|------|------|
| 目录分离 | 良好 | agents/skills/optional-skills/templates/scripts/tests/docs 分层清晰 |
| 命名一致性 | 一般 | 脚本命名有下划线(snake_case)和连字符(kebab-case)混用 |
| 依赖方向 | 清晰 | devkit.sh -> 子脚本 -> lib_manifest.sh，无循环依赖 |
| 文档覆盖 | 良好 | 42+ 文档，26 个 runbook，NAVIGATION.md 导航 |
| 文档准确性 | 差 | 版本过期、引用缺失脚本、NAVIGATION 引用不存在的文件 |

### 11.3 维护和扩展隐患

| 隐患 | 严重度 | 说明 |
|------|--------|------|
| 跨脚本重复函数 | 高 | to_lower/resolve_profile_items/run_cmd/frontmatter 解析各重复 2 次 |
| 两种 trigger 系统 | 高 | 新增 skill 时不知用哪种风格 |
| 工件模板桩文件 | 中 | 扩展时需从零填充 |
| 运维脚本无路由 | 中 | 用户无法发现 health/backup/monitoring 等功能 |
| rg 依赖未声明 | 中 | 4 个脚本隐式依赖 ripgrep |
| 交互式 read -p | 中 | CI 环境会挂起 |
| 版本号分散 | 低 | 6 个文件各管各的版本，无单一来源 |

---

## 十二、综合评分

| 维度 | 得分 | 满分 | 说明 |
|------|------|------|------|
| 架构设计 | 8 | 10 | 分层清晰，核心管线职责明确 |
| Agent 质量 | 9 | 10 | 零冲突，结构统一，中文质量优秀 |
| Skill 质量 | 7 | 10 | 内容扎实但 trigger 系统混乱，3 组重叠 |
| Profile 设计 | 8 | 10 | 继承正确，1 个冲突不对称，1 个缺 trigger_examples |
| 脚本工程 | 6 | 10 | 核心管线好，但重复函数/死代码/交互式 read |
| 意图路由 | 2 | 10 | routing 表设计了但未被消费，match 0/7 命中 |
| 模板完整性 | 4 | 10 | 顶层模板好，工件模板 7/8 是桩 |
| 测试覆盖 | 7 | 10 | 25 测试全通过，但不覆盖 match 功能有效性 |
| 文档准确性 | 4 | 10 | 版本过期、引用缺失、NAVIGATION 断链 |
| 实际可用性 | 3 | 10 | 从未部署到 ~/.codex，match 不工作 |
| **综合** | **58** | **100** | |

---

## 十三、修复路线图

### 阶段 A: 阻断修复（P0，预计 2h）

1. 修复 skill_match.sh — 消费 manifest.yaml routing 表，而非仅读 SKILL.md triggers
2. 删除或差异化 enhanced-gate-check.sh（与 quality-gate-check.sh 完全重复）
3. 同步 .version-lock 到 2.0.0
4. 修复 install.command 与 default_mode 矛盾
5. 清理测试产物 docs/changes/archive/20260505-test-e2e-001/

### 阶段 B: 高优修复（P1，预计 3h）

6. 统一 trigger 风格 — 全部改为可匹配关键词短语
7. 补齐 10 个 skill 缺失的 version + last_updated
8. 修复冲突不对称: release-hardening.conflicts_with 加入 large-refactor
9. 补齐 adk-artifact-gated-lite 的 trigger_examples
10. 将重复函数收入 lib_manifest.sh
11. 添加 rg 依赖检查到 health-check.sh
12. 消除交互式 read -p（改用 --force 门控）
13. 修复 performance.sh 破坏性 sed 操作

### 阶段 C: 文档修复（P1，预计 1h）

14. 更新 commands.md/usage.md 版本号到 2.0.0
15. 创建 docs/skill-routing.md 或从 NAVIGATION.md 移除引用
16. 标注跨仓库脚本引用（check-global-codex-health.sh 等）

### 阶段 D: 质量提升（P2，预计 4h）

17. 填充 7 个桩工件模板
18. 为运维脚本添加 devkit.sh 路由或独立文档
19. 增加 match 功能有效性测试
20. 解决 3 组 skill 重叠（合并或明确差异化）
21. 执行 ~/.codex 真实安装验证

---

## 十四、一句话总结

**骨架优秀（Agent/Profile/Core Pipeline），肌肉不均（Skill trigger 混乱、模板桩文件），神经系统瘫痪（路由不工作），从未在真实环境跑过。完成阶段 A+B 后可达"团队可用"状态。**
