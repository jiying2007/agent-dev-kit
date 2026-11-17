# 负结果

- 本轮启动时，旧 RTK 路径与 PATH 中的 `rtk` 均返回 exit 127；旧工作树的 `.git` 指向已不存在的另一 scratch 路径，Git 读状态返回 exit 128。没有修改或重建这些旧工作树，改从远端精确 main 创建新 checkout，原文件保留。
- 仅为恢复工具执行最小 bootstrap：从 RTK 官方 v1.2.0 Release 下载 x86_64 musl 二进制，核对官方 asset byte size 与 SHA-256 后使用；未运行安装器或修改宿主 hooks/runtime。archive 7111018 bytes，SHA-256 `70fee7b4a548c43dde94c77e2335550981b0bc2fb013691d8c8109b5bd0eda37`，binary SHA-256 `8a64af588cabed12eca467d407e3d63c05b3a9b7afc308c2dda75489f7270dfb`；`rtk --version` 返回 1.2.0。
- 按 R1.8 查询 `knowledge/L2-domain/lessons.md` 时返回 exit 2，文件不存在。不能声称查到了适用历史教训；继续通过已存在的 change 原始证据核对上一轮已修问题。
- Root 的 Knowledge Provider 原入口执行 exit 127，`/home/agent/codex/scripts/knowledge-provider.sh` 不存在。保持 unavailable；本轮不安装运行时或写入长期 memory。Root 首次 clone 遇网络 CONNECT 403，后续只读 ls-remote 成功后重试正常，精确 HEAD 为 5e29f69。
- 首次源字节统计命令的嵌套 shell 引号错误，未进入 Python；改用直接 RTK Python 调用后完成实际统计。8 个现有 ratchet 全通过，large-refactor full source 323144/323328，incident-response 46534/46612；不是 Token 测量。
- 嵌入式新验收在旧源码上复现 RTOS 方法条件失败和 5 个路由失败；首次 BSP-only 领域条件又排除了既有 SoC board 正例，补回 BSP/SoC 后 12 条路由通过。旧失败与中间失败均保留，不只保存最终绿灯。
- Workflow 新验收首次 RED 为 7 methods、19 failing subtests、14 errors；首轮修复仍在“不涉及量产或 OTA”上失败，后续收窄到具体 OTA 动作上下文后通过，并保留只读 OTA 回滚正例。默认 Python 缺 Ruff 的环境错误另记，使用隔离 quality 工具后的真实结果另存。
- context/optional 首份报告把 core + 9 optional 的导出覆盖概括为 20/20；原始 probe 实际为 16/20。缺席四项不属于该 profile，不是 compiler 丢失。更正以追加记录和 team-core 对照保存，原 baseline 不覆盖。首次测试入口同样用了错误 profile，该错误不计作产品 RED；正确 profile 下有效 RED 为 5 项、11 failures、0 errors。
- 人类派工信封与 canonical v2 的差集为 11 个缺失字段、17 个额外字段；早期人工消息将后者误计为 18，原 validator 返回未修改。
- 初稿与中间稿曾分别超过 large-refactor full-source 原限额 350 B、53 B；通过精简重复语句而非改限额收敛，最终值以整合测量为准。原超限结果保留。
- 目录生成入口检索时引用了不存在的 src/agent_dev_kit/catalog.py，rg 返回 exit 2；实际权威为 catalog_contract.py，随后通过现有 catalog build 生成投影。
- 新的独立终审复现两个适用任务回归：三种真实 OTA 任务，以及 VxWorks 任务设计，旧基线可选而首稿 abstain。原始审查报告及 probe 单独保留；继续修正领域条件，不能以已有测试全绿代替这些正例。
- 首次整合完整回归在独立审查确认 OTA 回归后主动停止，原会话返回 exit 130，日志有 42 条完成的 PASS；这不是 102 项全套通过。单独 exec 的进程查找没有看到该会话，断言失败且未发信号；随后对原会话发送 Ctrl-C 成功。最终修复冻结后另跑全套，不覆盖旧日志。
- 本轮 Git push 的无写入 dry-run 返回 exit 128：当前命令环境不能读取 GitHub Username。没有从连接器提取凭证或修改认证配置；后续使用已有授权 GitHub Git Data 接口传送已审核 tree，并逐项核对本地/远端 Git tree 身份。
- 最终双目标导出验证器的首稿错误地要求复制所有 Skill 根目录文件，因 34 个仓内 README/LICENSE/agents UI 元数据未分发而返回 AssertionError。实际既有 target contract 只声明 SKILL.md 与 references/scripts/assets/templates/examples；没有改 compiler 或该合同。按原合同核对后，两个目标各 65 个正文及 54 个支持文件齐全且摘要一致，保留这次验证器范围错误，不计作产品修复。
- 第一遍完整结束的 regression 为 102 套件、101 PASS、1 FAIL（345.142 s）。失败为 test_software_m5_ready：固定 60 路由集的 route-054“立即进行 SSH调试：登录生产设备，抓取日志并执行诊断命令。”应由 embedded-debug-transport 接收，新增泛“诊断”全局路由却选 systematic-debugging，确定性集为 59/60。保留原 fixture 和 expected owner，修复通用诊断相对专用意图的优先级后重新验证；不得把原全套日志或历史资格改写为通过。
