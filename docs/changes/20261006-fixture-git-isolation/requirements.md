# 临时 Git fixture 隔离需求

目标：只加固 tests/test_runtime_bundle.py 的合成仓库创建，避免继承调用方 Git 仓库指向、配置、hooks、template、签名和自动维护。基线为 main 19dafa7c61355c04c08e87adcf3eae6946020f92，版本保持7.14.1。

验收：敌意 Git 环境下仅提交指定 fixture，外部仓库 HEAD 和 index 不变、hook 不执行、template hook 不复制；fixture 显式禁用 GC/maintenance 及 detach。原两次独立构建、可复现身份和 dirty-source 拒绝断言全部保留。定向测试、完整回归和差异审查通过后才进入已授权提交及条件合并。

边界：不改变生产源码、manifest、版本、lock、CI、发布或 clean/dirty 判定。不调用真实模型，不修改用户配置。官方第一次CI的具体后台writer没有证据，本变更只声明隔离加固，不宣称原偶发清理错误的确定根因已关闭。
