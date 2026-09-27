# 设计：Python 3.8 兼容迁移

## 已知阻断

- 83 个源码 Python 文件中，`distribution/release_artifacts.py` 的括号式多 context manager 是唯一 3.8 语法错误。
- 5 个模块导入 3.11 才有的 `datetime.UTC`；`versioning.py` 使用 `zip(strict=False)`。
- `pyproject.toml` 当前声明 `>=3.11`、`setuptools>=77`、`jsonschema==4.26.0`；后者要求 Python >=3.10。
- doctor、发布契约、CI、依赖回执及版本门禁对 3.11/3.12 有固定期望，必须随真实验证一起迁移。

## 实现顺序

1. 先以隔离 CPython 3.8.10 + PyYAML 6.0.3 + jsonschema 4.17.3 建立导入和 Schema 探针；jsonschema 4.17.3 在 3.8 提供 Draft202012Validator。
2. 使用 3.8 等价标准库写法替换语法/API，不增加运行时猴子补丁；保持版本比较、时间戳、压缩包和信任验证结果不变。
3. 统一修改依赖、医生、SBOM、发布和 CI 声明；3.8/3.11/3.12 对同一输入跑确定性测试。
4. 源码验证后再处理 Codex 精确来源与安装，不把 ADK 源树直接写到 `~/.codex`。

## 当前实现选择

- Python 3.8/3.9 固定 `jsonschema==4.17.3`，Python 3.10+ 保留 `4.26.0`；两边均使用 Draft202012Validator，行为由相同的 Schema 负例验证。构建后端在 3.8 使用支持该版本的 setuptools，并使用兼容的 PEP 621 license 写法；wheel 仍包含 LICENSE。
- Python 3.8 通过标准库 `timezone.utc`、流式 SHA256 与 `resources.open_binary` 实现等价行为；冻结 dataclass 在 3.10+ 继续使用 slots，3.8 保持冻结字段语义。
- 3.8/3.9 质量工具使用独立固定版本，3.10+ 保持现有质量工具；`tomli` 仅供 3.8/3.9/3.10 测试读取 TOML。旧 Debian 11 基础镜像仅作为无凭证、离线执行的 CI 工装，APT 来源固定为其声明的历史 snapshot；不作为运行时发行基础。
- quick 测试在 3.8 的实测约 149 秒，因此只为 3.8 设 180 秒预算；3.11/3.12 保持 120 秒。预算仍有严格失败负例。

## 回滚

源码改动逐文件可逆；本 change 不执行远端发布或 live apply。现有 Codex 本机两份 apply plan 与备份保留为运行态回退锚点；3.8 迁移失败时维持 ADK 7.8.0 已提交来源，不修改其 tag。
