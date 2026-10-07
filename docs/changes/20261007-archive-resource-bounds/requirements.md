# 归档资源边界

目标：release artifact verifier 与实际 release extraction/rehearsal 不得在JSON预算前无界读取归档元数据或解压流；摘要与解析绑定同一次有界regular文件快照。
范围：typed distribution archive IO、release contract、release extraction入口及确定性回归；Root消费精确新来源并补消费测试。保持schema、有效制品摘要算法、输出格式和资格边界；不改变Skill/Agent/runtime policy正文，不调用真实模型。
验收：压缩/实际解压字节、成员数量、单文件、名字、隐藏扩展header读请求均有上限；缺失/重复/特殊critical成员、坏CRC/截断与叶链接/FIFO拒绝；完整8.0.3实际制品兼容。解析与SHA来自同一快照，提取前先做有界预检。
边界：有限字节预算不代表墙钟/精确OS内存上限；外层OS限制仍必要。调用者控制parent/writer，descriptor不承诺同UID干扰或目录rename防御。非法归档有意变为fail-closed，未支持安全descriptor的平台不引入fallback。
