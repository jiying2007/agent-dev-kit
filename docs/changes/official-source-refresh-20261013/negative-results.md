# 负结果与限制

- 原 canonical ADK ef538 的 opencode source 于 2026-10-11 到期，OWASP source 于 2026-10-12 到期，五项 Anthropic source 于 2026-10-11 到期；root forced CI 38268577043 因真实过期 gate 失败并跳过签名 job。
- 原 root 单测试修改只能验证拒绝语义；ADK quick 当时 48/56、root quick 44/52，不能解除生产 source gate。该阶段已按依赖失败 aborted，root 候选保持未提交。
- OWASP 官方指南 download/52117 两次 web 读取 timeout；本 change 的复核依据是实际可读官方落地页与完整列出 ASI01-ASI10 的发布说明，不是指南全文。
- 初版来源修复 source 8.0.5 full 98/98、最终 source 8.0.6 quick 56/56 与 full 98/98；没有忽略测试或放宽 expiry。
- 历史 runtime run 38260430071 在模型命令前失败，未生成 runtime 签名。整个 M5 真实模型取证上游请求仍为 0。
- 本地 source/release contract PASS 不能代替新 exact main 签名 promotion、immutable release、root import、runtime measurement 或 human field/owner 资格。
