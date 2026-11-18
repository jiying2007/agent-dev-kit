# 最小设计

`agent_dev_kit.manifest_query._load` 改用 `strict_json.read(regular_only=True)` 并设置 16 MiB 上限。原 shell 查询协议、输出结构和大流消费不变；添加对应真实 subprocess 负例。与尚未通过版本门禁的 Dependabot 依赖更新合并为有实际质量收益的 ADK 版本，保持全部 SemVer 投影一致。

不更改 Root、用户 Home、Native 验证、发行签名或质量证据；独立发布后再由 Root 精确升级。
