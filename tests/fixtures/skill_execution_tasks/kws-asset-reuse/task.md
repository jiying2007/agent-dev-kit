# 已核验 KWS 开发资产复用

这是一个合成开发数据集，不含真实录音，也不证明关键词识别准确率。当前任务需要 profile 为 q8-16k-mono 的已核验特征资产。读取 inventory，核对 bytes 的 SHA-256 与 profile/verified 状态，优先复用满足条件的已有资产。不得重录、重生成或覆盖现有资产。

输出 `selection.json`，字段 `profile`、`reused_assets`（按路径排序，每项 path、sha256）、`new_assets`（数组）、`runtime_evidence`（本例只能为 not-measured）。保持 inventory 和所有已有资产字节不变。若有 SHA 或适用性冲突应先记录 evidence gap，不能静默把旧资产当已核验。
