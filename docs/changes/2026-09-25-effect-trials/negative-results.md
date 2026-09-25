# 负结果

新增安全护栏用例最初构造了“succeeded + failed guardrail”的矛盾 fixture，现有 trace validator 正确拒绝。已改为 failed/validation-failure 与 first_pass_success=false 的真实语义组合，不放宽原 validator。

代码审查发现候选安全失败与基线安全失败必须区分：候选失败否决收益；用于对照的基线失败不能错误否决已修复候选。分别增加回归测试。