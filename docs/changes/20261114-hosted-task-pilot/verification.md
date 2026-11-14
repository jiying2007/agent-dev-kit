# H3 验证与执行来源

执行源码固定为`b8815263a31ee3b004c2e7e9eee564fe8a35dfc8`（C2），tree为`cb856f4b51fbe10eeac71a396f7cb87ca55e407e`。它是首次审查提交`887f0c6a10b03b57280865c6db677e4d9579c85c`的正常后续提交；两个核心模块未变，仅修订workflow、合同测试及相关合同说明。原C没有触发模型，其101/102完整回归和requires-changes裁决独立保留。

| 验证 | 实际结果 |
| --- | --- |
| 定向合同 | 17 tests，1.164秒，OK；包括真实本地进程组超时与工作流fallback shell |
| 前置失败与部分执行 | 3个fallback测试实际执行4种合成场景，核对skipped、unknown与原摘要/manifest字节保持 |
| 原失败product-maturity | 新定向复核PASS，完整回归也PASS；scanner和拒绝语义未弱化 |
| 静态、类型及体积 | Ruff、格式、mypy strict的3个文件、现有module-size/architecture全部exit 0 |
| 完整回归 | 102/102，exit 0，stderr为空 |
| 独立只读审查 | Spec/Quality pass，open blocker/major为0；精确绑定C2及8个冻结文件 |

完整回归实际起止为`2026-11-14T16:01:29.480448Z`至`2026-11-14T16:06:13.335802Z`。stdout SHA256为`0d1bee4e82001511f12291d9c3be0867228a5a396f58b49d3acd176ef3eed61e`，stderr为空文件。原始输出和计时在`evidence/full-regression.json`中以可逐字节还原的UTF-8文本保存，内含每份原件的摘要；不是重新执行或重写结果。

作者的六组实际命令、退出码及完整输出收录于`evidence/author-validation.json`。其原始manifest的14个成员已由独立审查者逐项复算。输入身份审计和无推理配置探针分别保留；原配置探针因本地namespace权限拒绝而未启动OpenCode，不能作为原生配置接受或Docker通过证据。

独立C2裁决时间为`2026-11-14T16:07:25.979218Z`，原件SHA256为`e599d4a33af8ed215823e2886ffd7db6ff9789f3898233fecb7fbd0f455f4898`。后续回执提交只保存本节、审查与验证材料、H3状态，不改变C2执行源码；执行分支仍从B/c57一次前移到C2，不前移到回执提交。

H4尚须取得公开job的真实模型/镜像digest、Docker隔离和原生配置资格；H5须独立审阅原件并调用既有grader。`bootstrap-status.json`是workflow新增的独立元数据，需要单独绑定摘要，不视为已受native manifest覆盖。源码通过不表示任务已运行或收益已成立；消费者原生门禁和正式发布资格也不由本次审查授予。
