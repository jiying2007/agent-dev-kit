# 验证失败与修复

## 2026-11-18：候选文档结尾空行

- 输入：PR #285，head `cba78132e84793e2f16fbc3ec80b8309b2e00a16`。
- 原件：[CI run 44207077191 / contract-py3.12](https://github.com/jiying2007/agent-dev-kit/actions/runs/44207077191/job/134475662953)。
- 实际结果：strict validation 通过；`Validate format and shell contracts` 因 10 个修改文件新增 EOF 空行失败，后续步骤未执行。
- 原因与修复：源文件快照写入时多保留一个终止空行；仅删除多余 EOF 空行，保留单个 LF。不修改格式检查、测试或预算。
- 验证边界：修复后必须使用新 head 的原 CI 回执；此记录不是重新验证通过的声明。旧失败原件保留。

11.4.2 发布运行 `44140561472` 的 ADC/CMake 超时属于已有历史失败，本次不改变其结论或标签；11.4.3 使用自己的发行链验证，不能继承诊断运行的通过结论。
