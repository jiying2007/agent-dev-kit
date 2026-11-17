# 方法组负结果

- 基线：0973b9dce75e7bde289a9915fc58dfd53cb79b0d / 11.3.12。
- 新增验收回归在改动入口前实际运行，4 个 test、5 个失败子项：perf 通用 LLC 标签、growth 过宽前置条件、rg 漏两个嵌套入口、两种 team-core 导出的 Root helper 条件。原始输出与字节哈希见 red-tests.raw.json；red-tests.txt 为移除行尾空格的展示副本；退出码 1 不计成功。
- 首轮修改后定向 17 项通过，但 profile-ratchets.json 显示 large-refactor 超出原阈值 110 B。没有提高阈值；只在本组 production-field-readiness Goal/参考与 artifact 条款中合并重复表述。后续结果另存，旧失败保留。
- 阅读辅助命令曾假定存在 tests/test_skill_contract_methods.sh；实际只有 Python 模块并由 test_skill_content.sh 注册。改用已存在入口读取，不计产品失败。
- 所有观察均为源码/确定性方法范围；没有付费模型、真实网络客户端、设备、HIL 或生产率结论。
