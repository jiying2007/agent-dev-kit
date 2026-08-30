# 负结果：privacy-ref-hardening-v1

| 修改前探针 | 修改前结果 | 根因 |
|---|---|---|
| Graph generated_at=2099 | pass | 只解析时间格式，不比较 as_of |
| Graph verified_at 晚于 expires_at | pass | 无 chronology gate |
| Graph retention=expire 且 expires_at=null | pass | retention 与 expiry/edge 未关联 |
| Graph owner=ghp_... | pass | 各模块 secret taxonomy 不一致 |
| Trace verification.evidence_ref=github_pat_... | pass | evidence_ref 是自由 identifier |
| Receipt evidence_ref=ghp_... | pass | evidence_ref 是任意字符串 |
