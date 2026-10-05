# 设计

文件解析使用 object_pairs_hook 检查每层重复键；发现重复键时返回 ManifestError，不输出键值以免泄露输入内容。保留既有字节上限、schema、finite number、完整 trial population 和 test-only 权限边界。

全回归在计算绝对 ROOT_DIR 后切换至该目录，使 tests 包和基于 Path.cwd 的测试引用 ADK。不更改调用者 shell 的目录；相对 --timing-json 路径仍按调用者原目录解析，保留原输出契约。

外部依据：Anthropic agent evals 强调稳定测试环境、完整 trial 和 outcome；这里只硬化本地已有实现，不导入外部 runtime。
