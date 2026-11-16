# Git 二分日志兼容：实际验证

本记录承接 PR #275 首次远端失败，原方法审查与完整回归保持历史身份。基线是 `bc2f4b2ca3bbef2cb5515322048a144639e79004`；本次受审 source 是 `f23d41e2a4d7e4ea5b5cb392f514827d01178ed8`，tree `1197f5560a7a8fc03f5454dfa16460da8c2a108c`。5 个改动文件与 6 个未变方法文件的身份见 [source-bindings.json](evidence/source-bindings.json)；本次完整差异 SHA256 为 `78f40cc8970c097e427e20e8c59a06dfc3e595a9186719fac162e1e468a068e4`。

## 已发生的验证

| 观察 | 实际结果及边界 |
|---|---|
| 原 CI | Git 2.56.1；PR head bc2f4b2，实际 checkout 为 PR merge commit `f6a34cc5dc329268b9028c3e5aee7328e01973ee`；101/102 组、内容组 152 项中的 3 项失败。完整原日志保留。 |
| 原本地基线 | Git 2.52.0，原 5 个真实 Git 案例通过；不能推导新版 Git 已通过。 |
| 确定性 RED | 加入真实日志格式回归后，10 个方法运行、8 个子断言失败；旧 5 案仍通过。 |
| 修复后 GREEN | 10/10 方法通过，0 failure/error；两格式的终局正反检查、唯一记录、完整 SHA、歧义标题与原有真实 Git 语义均保留。 |
| 内容入口初次 | 157 项完成，但 PATH 缺少已安装 CMake/CTest，14 个子项 skip；没有当作完整覆盖。 |
| 内容入口纠正 | 恢复原完整验证使用的 CMake 3.31.6 与 ninja PATH，157 项通过，无 skip，2026-11-16 14:01:13.424501 +08:00 完成。运行中仅发生相同字节文件入索引，没有源文件编辑；不称为 clean HEAD 完整回归。 |
| 独立复核 | 独立 10/10 定向测试及 6 个实际 CI 文本探针通过；准确来源的 Spec/Quality PASS，IR-CI1 major/closed，关闭范围为源码修复与已执行证据。 |

完整 Skill 内容入口由原 152 项增加至 157 项；本轮最初增加 12 个测试，CI 跟进再增加 5 个格式回归，合计 17 个新增方法。没有删除原有真实 Git 案例、跳过失败案例、调整 CI 或增加门槛例外。

[作者 RED/GREEN](evidence/parser-red-green.json)、[独立报告](evidence/independent-source-review.json)、[支持环境内容回执](evidence/supported-content.json)、[初始跳过回执](evidence/initial-content.json) 和 [原 CI 日志](evidence/initial-ci-regression.json) 分别保留。两份 retained-files 索引映射原执行路径到保留副本。原 CI 与首次 skip stderr 含真实尾部空白，使用 JSON 文本字段无损保存；解码后的原始长度/SHA256 与封装文件的长度/SHA256 分开记录，未修剪日志或放宽空白检查。

本地没有执行 Git 2.56.1；实际 CI 文本回放不是新版 Git 运行。本次没有重复无变更生产资产的本地 102 组回归，原先 b4c2a 的 102/102 不转记给 f23d41e。**新 PR head 的完整远端 CI 必须通过后才能合并**，其真实结果以及后续 main/release/Root 接入记录在 PR；本文件不预填后续平台成功。

原 4 个 Skill 方法、配置、CI、版本和原审查记录保持不变。本次不建立原生加载、RTOS/HIL、硬实时、模型 A/B、Token/成本或产品/现场资格。
