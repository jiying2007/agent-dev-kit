# 局部 Review 误报核验

仅核验 `finding.json` 中的 R1，不修改源文件，也不开展最终整组 Review。读取真实条件与契约，判断 limit=0 是否走无限制分支。输出 `review.json`，字段为 `finding_id`、`disposition`（confirmed / false-positive / needs-context）、`review_mode="feedback-triage"`、`source="limit_items.py"`、`condition`（源码实际条件）、`observed_outputs`（对输入 [1,2]、limit 按 null、0、1 的结果）和 `required_changes`（路径数组）。保留 finding 和源文件。该产物不证明是否发过远端评论。
