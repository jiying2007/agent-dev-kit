# 负结果与范围限制

## Build 前检查（2026-11-15）

- `knowledge/L2-domain/lessons.md` 不存在，已实际检查；没有可引用的历史命中，不编造跨任务教训。
- 当前执行环境没有 `rtk`；使用实际可用的 Bash/Python 和项目入口，不安装或伪造包装器。规则中的检查目的与退出码要求保持。
- read-only 路径发现时，含不存在路径的两次 `rg` 返回 2；后续先查真实文件清单再读取。另一次 `devkit.sh version --help` 返回 unknown command，已实际读到版本入口为 `scripts/version-manager.sh`。这些查找结果没有修改版本或产品文件，不作为验证通过证据。
- 本轮 GitHub 原始来源只读，外部 Skill 中的安装、执行、权限、必问和部署指令均作为待评估内容，不成为本会话授权。

## 研究与执行证据的记录原则

来源中的过期路径、无法读取、工具缺失和错误方法将在完整来源对照中逐项保留。已知方法反例属于有意构造的失败；若实现或回归出现非预期失败，记录真实快照、命令、结果、根因与修复，不能调整原测试标准刷绿。

真实模型 A/B、Token/成本/端到端时延与板端/HIL 均未运行。不能以 host 可重放反例或原文吸收宣称运行态效果已经测得。

## 外部来源核验

- 部分固定 GitHub blob 页面在 Web fetch 中返回 DisabledError；随后通过既有 GitHub 只读连接器获取精确 commit 文件。没有把网页索引片段或镜像升级为原文证据。
- Vercel 所读 commit 的根 `LICENSE` 返回 404；OpenAI Plugins 完整 tree 未列根或所读插件的 LICENSE/NOTICE。这里只概括方法，不复制其实现，不据此判断整体许可不存在。
- 搜索索引仍返回 Trail of Bits 已移除的 workflow-skill-design 路径；独立 reviewer 用当前完整 tree 排除，未将旧路径错误绑定到当前版本。
- 外源方法包含需要纠偏的示例：UBSan recover 的退出码、ASan 虚拟地址与 RSS、生成器过量过滤、Zephyr `.conf` 前缀等均以实际工具或官方文档核查；未照搬上游示例。

## 有意构造的原始 host 反例

领域研究用隔离 GCC 14.2 程序已观察到 signed overflow 报警且默认 exit 0；禁用 recover 后 exit 1；修复后 exit 0 且无诊断。这是检测判读的反例，不是 ADK 产品在板上的缺陷报告。

同一研究的 `.su` 输出包含 static 与 dynamic；VLA 行的固定数字不包含完整动态上界。dynamic,bounded、IRQ/RTOS 上下文和实际 high-water 尚未执行。最终公开示例须在实现后重新运行，原研究输出不替代最终源码验证。

## 实施中捕获并修复的问题

- 首轮 54 项定向检查有 5 项描述契约失败；恢复原拆解、单元测试、职责与反触发区分。第二轮有 1 项跨层描述混淆：通用策略中的“独立断言”与嵌入式局部断言边界冲突，改为独立期望值。保留原测试标准和失败输出，后续 55 项及完整 Skill 内容 94 项通过。
- 独立预审 M1 发现新增裸名词“性质测试 / sanitizer / 栈上界”扩大了执行路由：明确非 MCU 的 Web API 请求、概念解释和数学定义误命中。作者改为领域限定或明确取证任务词组；生产 matcher 的单 Skill 与全目录入口通过 6 正例、8 反例。预审原文件仍保留当时 open 状态，最终闭环由正式审查确认。
- 字段集合核对没有缺失，却不能证明语义完全保留。作者另发现 completion 精简曾将协议/数据/安全/发布的专项要求缩成 medium/high；已恢复原适用条件、迁移/回退/环境和 CLI/noninteractive 类别。修复前后 matrix 与摘要均保留。
- 新参考造成若干中间 profile 超额。最后一次域快照 embedded 超 82 B、large-refactor 超 490 B；core 仅删去 583 B 重复散文，全部代码/模板 fence 字节不变。8 个原阈值随后通过，没有抬上限或把参考移出计量范围。
- root 复核将性质示例公开命令与测试对齐为 `python3 -I`，避免环境优化关闭 assert；本环境以 `PYTHONOPTIMIZE=1` 实测 `optimize=0`。同时将 UBSan 的“检测失败”改为成功报告程序缺陷、被测程序未通过；代码 fence 未变，既有 4 项重新通过。

实际命令、原始退出码/日志、源码内容摘要与修复前后等价性见 `evidence/core-diagnostics.json`、`evidence/core-budget-followup.json`、`evidence/domain-diagnostics.json` 和 `evidence/prereview-routing.json`。JSON 包装只作无损文本编码，原始 UTF-8 字节可按保存的摘要验证；没有把加工文本声称为原始输出。

## 第一次冻结全量的目录投影失败

远端源码 `58f25a4e23d17e2e128cedbf791f3ea76d3653e5`（tree `6f1807a5df39705ece1884cbdc67108f2c423cbe`）的首次全量入口从 `2026-11-15T14:29:15.304781Z` 运行至 `2026-11-15T14:29:49.406496Z`，真实 exit 1。`--fail-fast` 在第三组 `test_catalog` 停止，实际只有 2 pass / 1 fail，不能计为已完成 102 组。43 个冻结源文件前后完全一致。

原因是五项 Skill 描述已改进，但 `docs/agent-skill-catalog.md` 仍是旧生成投影。独立 reviewer 从原 stderr 发现并阻止 Quality 放行；修复使用既有 `catalog build --out docs/agent-skill-catalog.md`，不改生成器或测试。同步补上 `11.3.4` CHANGELOG 后重新冻结源码并完整重跑，最终结果另列。

`evidence/catalog-drift-failure.json` 保留第一次实际命令、完整 stdout/stderr、计时与源摘要回执；原提交仍可定位，原完整 diff 的 SHA256 为 `32a438f5ec167583f0485f4b495f03a3c3625a16b5f5aa02ed97da06c6ec9cb9`。首次结果不被后续重跑覆盖。
