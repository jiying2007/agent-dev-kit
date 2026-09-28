# 设计与取舍

[Langfuse 版本化数据集](https://langfuse.com/docs/evaluation/experiments/datasets)强调实验绑定所用数据版本。本地 ADK 不引入服务或 SDK；只把 source/test 评测绑定到每次实际读取的有限字节。

`run_effect_eval` 将输入和标签路径安全核对后各读一次，计算读取字节的 SHA256 并与合同值比较，再用同一字节解码、解析和评分。输入 parser 保持原有字段与唯一 ID 校验。报告新增 `snapshot_atomic=false`，避免把两个分别读取的文件误称为原子快照。执行前后的路径漂移不会改变这次内存中的评分内容；若要证明外部来源不变，仍需独立来源锁与签名证据。
