# ADK 9.0.0 — 构建 Python 与部署 Skill 解耦

- 9.0.0 重大版本，来源 ADK 8.2.3 protected main 573452b0ac07dc5464469f09b6825183b2ada6ae，保留原版本不可变发行物。
- ADK 构建、管理 CLI、校验与发布最低 Python 3.11；CI 实测 3.11 / 3.12。
- 导出纯 Skill Runtime Bundle 不携带 ADK Python 源码、stdlib 兼容代码、虚拟环境或包依赖；独立 Skill 自有外部可执行依赖仍须单独声明。
- 移除 3.8/3.9/3.10 Python 兼容路径、旧固定依赖、Bullseye 备用镜像、自定义 slots/stream hash shim、废弃的 test extra 和支持该组合的失效测试。
- 非目标：修改 Runtime 自身使用的 Python 或其它语言依赖，改变已发布 8.x 版本，绕过 Reviewer、修改 source-to-live 或 Product M5 资格。
- Root 与其它消费端必须经过正式不可变版本的各自授权迁移；未核具体消费环境前不宣称下游迁移完成。
