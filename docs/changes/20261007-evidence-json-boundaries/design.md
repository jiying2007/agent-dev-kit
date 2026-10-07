# 设计与取证

当前 8.0.2 源的最小实验确认，目标契约 `_json_object`、晋级 `_load_release_contract` 接受重复 `status` 并采用末值；归档 `_canonical_manifest_sha256` 对歧义 JSON 计算规范摘要。晋级输出 `Path.write_text` 可跟随预置链接。

采用已有 `strict_json.read(regular_only=True)` 绑定打开描述符并设置 4 MiB/64 层限制；归档字节读取沿用原有 8 MiB 限制并使用严格 loads，不解包到磁盘。仅 packaged schema 仍可普通解析。输出沿用公开 0644、排序键、缩进和尾换行，校验生成文档后调用共享原子写入。

外部资料：Python 官方 JSON 文档提示不可信解码的 CPU/内存风险，默认解码接受重复键；POSIX open 规范说明 FIFO 无 NONBLOCK 时阻塞。链接：https://docs.python.org/3/library/json.html 、https://pubs.opengroup.org/onlinepubs/007904875/functions/open.html 。MCP 官方安全指南仅作扩展边界审查输入，本轮不新增 MCP 功能。

平台/兼容边界：不改变 schema、规范摘要或签名身份；有效来源字节的输出排序保持不变。严格 JSON 错误通过现有 ValueError/ManifestError 处理，不泄露输入内容。归档总成员/解压资源限制需单独评估，不能以本轮 JSON 限制声称整包 DoS 已解决。
