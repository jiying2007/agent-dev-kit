# 负结果与能力边界

- 基线主线和新 worktree 均为 `e13bd4788d5638c1eb34c169870f19dfd5285b6b`，新分支起点无 dirty 文件。
- Build 前按 Skill/CMake/timeout/context/Token 关键词准备检索 `knowledge/L2-domain/lessons.md`，实际文件不存在，未引用不存在的历史教训。
- PATH 中没有 `rtk`，本轮使用原始 shell/工具。PATH 初查也缺 `cmake`、`ctest`、`ninja`；随后找到另一受控临时目录已有 CMake wheel，仍需核实版本/来源后才能作为本机执行证据。`cc/file/size/objdump` 可用。
- 11.3.6 Release attempt 1 的 CMake shell 块在 15 秒整体预算处超时；相同源码的普通单次重跑通过。旧日志未打印已捕获的子进程输出，不能断言是 runner 抖动或已修根因。本轮仅基于新真实反例改善诊断和测试判定。
- 本轮不测外部模型/native agent host/板端性能，不将静态全文覆盖或源码字节变化称作模型成功率、Token/费用或设备效果。
- CMake 3.31.6 实测：全部动态 skipped 的原发布块返回 0；empty/all-disabled 在 `--no-tests=error` 下返回 8，较宽的 disabled false-pass 假设被反驳。首个 skipped fixture 使用了不存在的解释器，明确保留为无效探针，后用真实 `cmake -E false` 验证目标语义。
- 嵌入式新增测试首轮有一项夹具错误：GNU make 本身被置于含空格的临时 PATH 目录，递归命令拆开可执行文件路径。只调整工具目录；被测源码/构建目录仍含空格。37 方法第二轮为 32 pass / 5 本地 Ninja 缺失 skip。另一次直接内容测试漏 `PYTHONPATH=src`，保留 8 个 import error；按现有 wrapper 环境纠正后 39 项通过。
- 集成前检查中 strict/security/SOP 均通过，129 方法的 Skill 内容组因候选版本投影仍为 v11.3.6 失败一项；将 `tests/fixtures/skill_method_ab_prereg.json` 的 planned_release 同步为 v11.3.7。未改基线、case IDs、训练/holdout、not-measured、results 或验收断言，不能把这份未执行 A/B 计划当成四项对话试用的结果。
- 官方 Skill 来源补充检索的仓库根 LICENSE 路径 404；实际 Skill 局部 LICENSE.txt 已取得并核为 Apache-2.0。大检索响应一次尝试超出 shell 参数长度，未执行写入；按来源拆分保存成功，不改变来源内容。
