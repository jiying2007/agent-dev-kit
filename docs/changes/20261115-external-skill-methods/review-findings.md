# 独立 Spec / Quality 审查：外部 Skill 方法优化

## 裁决与身份

**Spec：PASS。Quality：PASS。未关闭 blocker / major：0。**

裁决对象是冻结源码 `cd1d9b316facff73bcec0ed39d3a942a959292e4`、tree `9020ba384be332dbd95575044da6b84313706c64`，以及下文逐文件绑定的本地验证和公开证据材料。此裁决允许进入既有受保护交付流程；不声明后续 PR CI、main CI、合并、tag、release 或产品/现场资格已经完成。

- Reviewer：`external_independent_review`（独立 AI 审核者）。
- 实现/整合角色：`external_core_methods`、`external_domain_methods`、`root`；与 reviewer 分离。
- Evidence completed at：`2026-11-15T15:04:06.254346Z`，对应最终公开材料补齐后的实际完成时间。
- Reviewed at：`2026-11-15T15:07:03.558091Z`，晚于第三次完整回归和最终材料完成。
- Reviewer 只读仓库；只写 scratch 审查材料，没有写需求、设计、实现、测试或发布修改，没有 commit/push。

本报告是实际语义审查声明与内容摘要绑定，不是已认证人类身份、GitHub approval 或密码学身份签名。

## 精确快照与材料

| 项目 | 绑定 |
|---|---|
| 基线 | `5e0e83bcc127665de9a352e9eacfe9b092106cb2` / v11.3.3 |
| 最终源码 | `cd1d9b316facff73bcec0ed39d3a942a959292e4` / v11.3.4 |
| 源码 tree | `9020ba384be332dbd95575044da6b84313706c64` |
| 源码范围 | 48 个相对基线变更路径；bytes / SHA256 / Git blob / mode 全部核对 |
| 完整原补丁 | 720111 B；SHA256 `6ef7ac27cc4c6bdde40dacf230731f4a320035f43c9531c8ca568f70ed148383` |
| 验证正文 | `verification.md`；SHA256 `18a909fa5de5193b2c8de1893c48e7052f7f0805bae24ce76239b4ba66ca288b` |
| 最终独立观察归档 | 93962 B，10 条原件；SHA256 `b132ceeb145f12467b6d653cdd6d3e7b46ce095ed3ab003cb3362fb404a202aa` |

完整逐文件清单见随本报告交付的 `final-binding.json`，发布时对应 `evidence/independent-review-binding.json`。它区分 48 个冻结源码文件和之后新增的 7 个验证/证据工件。后续机器记录只能机械映射本报告，不能改变结论、身份、时间、发现或证据范围。

阅读范围如实区分：本轮方法/测试源码及其最终修复全文；契约、逐项审查和来源决定；版本/目录/发布记录的完整变更；诊断归档的原件完整性和相关语义。CHANGELOG 等历史长文未重新审核全部历史。两作者对 65 项的覆盖和 143 条实际读取路径均核对到基线摘要/Blob；本 reviewer 没有冒称第三次独立精读全部 65 项正文。

## Spec 审查

| 验收范围 | 结论与实质依据 |
|---|---|
| 65 项完整范围与来源 | 39 + 26 个唯一身份对齐 Manifest 的 56 core + 9 optional；143 个路径摘要和 Git blob 无错配。6 项直接增强、1 项条件性交接、58 项保留有具体理由。采纳来源区分固定版本、选读范围、许可和拒绝项，没有把目录/star/摘要当作效果证据。 |
| 兼容迁移 | 普通纵向切片仍为默认；仅跨公共契约且有必要时 expand/migrate/contract，保留临时兼容 owner、退出任务、真实消费者和最终集成条件。示例通过真实子进程消费者暴露直接/过早删除失败。 |
| 独立 expected | 公开错误变体会骗过共享 helper，而独立契约常量能拒绝；正确实现和合法边界仍通过。没有将全拒绝或实现镜像当作可靠 oracle。 |
| checker 校准 | 仅新建/修改/可疑 checker 才触发；执行码、报告完整性、阈值分别判读。公开 scanner 只是受控报告回显，示例明确不证明生产扫描能力。 |
| property/stateful | 有界 FIFO 序列使用独立 deque 模型，121 序列/426 步与反例回放真实；最短结论严格限于给定有限字母表，未冒称 fuzz/HIL。 |
| sanitizer | GCC host UBSan 原例/禁恢复/修复例确实执行；报警伴随 exit 0 不当干净通过。工具、编译、runtime、诊断和目标边界均保留，ASan/TSan 未运行明确列出。 |
| 栈分析 | `.su` static、dynamic,bounded、dynamic 与调用链、IRQ/port、high-water 分开。host 288/432/48 B 是该构建观察，不是任务峰值或 MCU 最坏上界；未实测类别未写成通过。 |
| 入口与携带 | 按需参考保留自身文件依赖；跨 Skill 只条件性交接。7 项两目标历史导出与 completion 修复后的两次正文导出能对应到实际文件，关键条件不只留在被剥离的 frontmatter。原 completion 适用矩阵、生命周期、权限、快照/原始转录、非交互与 source-to-live 条件保留。 |
| 验证与交付 | 本地完整 102 组、原 profile 阈值、精确源身份和独立审查条件满足。受保护 PR/main CI 和 canonical release 仍需后续真实事件；本报告不提前关闭这部分交付验收。 |

## Quality 审查与已关闭发现

| 稳定 ID | 级别 / 处置 | 原问题与关闭依据 |
|---|---|---|
| `m1`（原 M1） | major / fixed | 可变预审中，裸“性质测试”“sanitizer”“栈上界”把非嵌入式或纯解释请求引到诊断方法。最终词收窄到 MCU/RTOS/嵌入式测试、sanitizer/UBSan 取证和 MCU/RTOS 栈评估。原三反例及其余解释/否定控制在生产 Matcher 测试中拒绝；领域 6 正例/8 反例同时核单 Skill 与 auto。独立另做 5 组既有 non-trigger × 两种选择，共 10 次真实 CLI 拒绝；auto 保留 abstain/deny。Matcher 与权限实现未改。 |
| `m2`（原 M2） | major / fixed | 首次冻结 `58f25a4...` 全量在 catalog fail-fast，真实 2 pass / 1 fail。原生成器更新五项描述投影，未改测试/生成器；第二和第三完整入口中的 catalog 均通过。首次完整原回执、日志和旧快照仍保留，没有把失败改为通过。 |
| `m3`（原 M3） | major / fixed | 第二冻结 `5f42c1b...` 在第 99 组 capability fail-fast，真实 98 pass / 1 fail。`delivery_goal` 为首报错；主文件亦缺 `affected_asset` 与模板入口，部分其他字段只在 frontmatter。修复将 11 个 Codify 字段/模板恢复到条件性正文，reference 回指自身入口；保留 goal-final/适用晋级、checkpoint-deferred 及效果/owner/rollback。独立两目标渲染确认约束元数据被剥离后字段仍在正文；三个 checker fence 和测试模块字节未改。原 capability 实际红→绿，第三冻结完整 capability 通过。 |

M1 为本 reviewer 的增量路由发现；M2 由本 reviewer 阅读首次真实失败回执确认并阻止放行；M3 为统一全量暴露、由 reviewer 进一步核对原检查器与正文可见性的问题。此前的“暂无新增源码阻塞”从未作为完整 Quality PASS；两次失败均触发重新冻结和完整重跑。

原 capability 四检查器、既有测试断言、Matcher、安装选择、权限和 8 个 profile 阈值没有被放宽。Completion 最后仅正文 +277 B、reference −262 B，净 +15 B；必要技术条件没有被字节预算替代。

## 实际验证与时间

第三次完整入口实际运行于 `2026-11-15T14:48:40.321722Z` 至 `2026-11-15T14:57:33.375706Z`，Python 3.12.14。命令为原 `bash tests/run_all.sh --fail-fast --timing-json ...`。注册数组、102 个逐组计时名称和 stdout 的 102 条 PASS **顺序完全一致**；mode=full、exit=0、summary 102/102、fail=0，stderr 为空。runner 532510 ms，外层 533053 ms；原入口未相对基线变更。48 个源码文件前后摘要相同、HEAD 未移动、运行结束工作区干净。

全量归档是该标准紧凑入口的完整原 stdout/stderr；不能据此声称保存了所有成功子进程的详细日志。独立新增模块实际在 `2026-11-15T14:28:24.517974Z` 至 `2026-11-15T14:28:30.556657Z` 运行，12 项、0 skip；原 stdout/stderr 已无损公开。历史执行保持其原快照，completion 后续文本变化通过相同代码 fence/测试摘要、定向正文渲染和第三次全量补齐，不倒填为旧时已执行最终文档。

最终机械证据对账 91 项均通过：源码/Blob/mode、注册组与日志、时间/分母、公开原件复制、10 条独立原件、嵌套失败记录、8 组当前 profile 数值、基线阈值和源码字节统计。该数量只是完整性核对项，不能加到测试任务或模型任务分母。最终阅读和语义裁决不由摘要匹配自动生成。

7 个入口为 32227 → 24488 B，减少 7739 B（约 24.0%）；本轮 Skill 文件合计净增 701 B。当前 8 profile 原阈值全部通过。它们是 UTF-8 源码量与确定性导出观察，不是运行期上下文 Token 或收益测量。

## 证据适用性与后续门禁

没有真实模型 A/B、独立最终 holdout、provider Token/费用/端到端时延、原生宿主实际加载认证、板端/HIL/IRQ/RTOS 最坏栈、设备或用户电脑操作证据。静态契约、host 程序和来源研究不能替代这些未测结果；外部 benchmark 也没有被移用为 ADK 收益。

本轮没有运行付费模型或第三方脚本、安装外部 Skill/依赖、增加运行时/后台巡检。原有 format 可执行位警告如实保留。集成者记录本地 ruff/mypy 不可用且未安装；本地 102 组不等于已执行受保护 CI 的 ruff/mypy/pip-audit/shellcheck。最终 PR HEAD 的必要检查、正常合并、main CI、annotated tag、canonical release 和制品状态由后续实际平台回执决定。

只要 48 个冻结源与这里绑定的 7 个证据文件未变，源码/本地证据的 Spec/Quality PASS 可用于原流程的下一门禁。若实现或受审证据变化，应按具体变更重新核对；本报告不为未审查的后续改动背书。
