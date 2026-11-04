# 设计与兼容边界

1. 版本以 SemVer 9.0.0 承认 ABI/运行环境下限变更，8.x Release 不变，先 ADK 审核与保护合并、main CI/immutable Release，再同步 Root。
2. 用 Python 3.11 原生 dataclass(frozen=True, slots=True) 与 hashlib.file_digest 替换 Python 3.8 compatibility module；不保留入口别名或过时垫片。
3. 统一 pyproject 内 3.11+ 的依赖版本，不维护重复依赖分支或空的 test 额外依赖。源码路由及业务语义不变。
4. CI 保留 matrix contract/regression 的全部失败聚合与 source-version 预检，但矩阵为 [3.11, 3.12]。本地 Docker 仅两种解释器，不使用已 EOL 的 Bullseye 3.8 重定向源。
5. scripts/devkit.sh 保留单一 Python 选择权威和 ADK_PYTHON_BIN 明确指定能力；低于 3.11 全入口拒绝，不再允许通过开关临时降低最小版本。
6. Runtime Bundle 自由于 ADK Python：明确只读输出资产与依赖边界；不得将 Python-free 推论扩大到任意自定义脚本、插件或者目标运行时。
7. 9.0.0 的 promotion-evidence 从 v1 明确变更为 v2（将源与 CI 声明约束改为 3.11/3.12），删除新发行物中的旧 v1 schema 而不是暗改 v1 意义。Root 当前签名 promotion_evidence consumer 的 REQUIRED_PYTHON 仍为 8.x 三版本。本 9.0.0 需要 Root 后续同源消费更新及签名原始证据，而不是在新版本 CI 中伪装兼容三版本。
8. Harness 七维 source-bound 旧签名对于 9.0.0 无效。必须有独立新审核、强制门禁、精确主线签名与 Root 正式受保护交付；发现失败如实保留。

历史 v1 的审计记录与不可变 8.x Release 保留原样；新 9.0.0 workflow 归档 provenance_authority 只输出 v2，不引入 v1 fallback。

三个独立消费契约 Workflow（Digital Worker、Codex、Claude）的离线校验只保留 Python 3.11/3.12，保留原协议身份/授权/无模型执行语义，消除最后的 Python 3.8 CI 轮次；这些入口不替代各消费端自身真实运行时要求。
