# 设计：privacy-ref-hardening-v1

## 共享合同

- identifier：小写、最大 128 字符的稳定 ID，且通过统一 secret taxonomy。
- opaque ref：固定 `ref:<64位小写SHA-256>`，不表达本地路径或用户文本。
- evidence ref：`ref/path/sha256` 封闭对象；path 相对 evidence root，禁止 symlink、越界与缺失，sha256 必须与文件和节点 content hash 一致。
- secret taxonomy：统一拒绝敏感 key，以及 GitHub/OpenAI/AWS/Bearer/private-key/raw-prompt/tool-payload 值模式。

## 时间和生命周期

- CLI/API 显式接受 `as_of`；generated/verified 不得晚于 as_of。
- `verified_at <= expires_at`。
- `retention=expire` 必须有晚于 as_of 的 expires_at。
- `supersede|retire` 必须分别存在 `superseded-by|retired-by` 出边。

## 回滚

回滚共享 validator、三个消费者和对应 schema/tests 即可；无 runtime/live 数据迁移。
