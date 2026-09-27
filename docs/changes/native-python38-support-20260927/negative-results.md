# 负结果：native-python38-support-20260927

| 尝试 | 失败证据 | 结论与修复 |
| --- | --- | --- |
| 直接用系统 3.8 导入原始 7.8.0 | `datetime.UTC` ImportError；83 个源码文件有 1 处 3.8 语法错误 | 替换为 `timezone.utc`、3.8 context manager 写法，并逐项保留行为 |
| 将原 `jsonschema==4.26.0` 安装到 3.8 | 包元数据要求 Python >=3.10 | 使用按解释器固定的 4.17.3/4.26.0，并验证 Draft202012Validator |
| 以 setuptools 75.3.2 构建原 pyproject | PEP 639 字符串 license 与 `license-files` 不受支持 | 采用兼容 license 表，wheel 检查仍含 LICENSE 与条件依赖 |
| 原 Python 3.8 Docker quick 工装 | Debian 11 安全仓索引指向已移走文件，APT 404 | 固定官方基础镜像已有的 Debian 历史 snapshot，仅用于隔离测试工具 |
| 3.8 quick 使用统一 120 秒预算 | 测试 48/48 通过，但实测约 149 秒超预算 | 仅给 3.8 设置 180 秒严格预算，后续 quick 与依赖审计通过 |
| 质量 extra 初版将 3.9 分配给 3.10+ 的新工具 | PyPI 精确版本元数据表明 `pip-audit 2.10.1`、mypy 2.3.1 和新 PyYAML stubs 要求 >=3.10 | 将旧版质量工具条件扩至 `<3.10`，不改变 3.8/3.11/3.12 运行依赖 |
| 将兼容提交迁移到上游 7.10.0 后运行完整矩阵 | 新增 `test_sigstore_blob` 的 `#!/usr/bin/env python3` 在隔离验证器的受限 `PATH` 下找不到容器解释器 | 测试夹具使用当前 `sys.executable` 的绝对路径，与既有 native trust 夹具一致；签名验证器的受限环境保持不变 |

这些失败均未作为发布或 live 通过证据；完整三版本门禁已通过，新的 clean 来源身份仍待形成。
