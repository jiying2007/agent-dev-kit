# 历史 probe 包装补充审查

这是归档后的证据格式修订，产品Head仍为d01d1bcb7c2f322c342656a95e523fba8b55505e，完整original.patch不变。C1 canonical和所有产品/测试/预算/门禁不变。

## 实际原因

正常lifecycle review在2026-11-17T15:21:18Z通过，archive在15:21:19Z完成，当时使用C2 canonical SHA-256 2f782d9a0a6bef04b89d6ff0f2f9757507bea8e39ef25db6d39189fb18c34d65。随后真实git diff --cached --check exit2，仅报告原始historical original_probe.py第19行的EOF空白行。独立审查者原样复现该失败。

该probe是既有不可变原始观察，不能修剪其尾部字节。现在只将它从original_probe.py封装为original_probe.json：UTF-8 content可还原全部1649 bytes，包括末尾空行，原SHA-256仍为26c7e0347f013ad30ba7376291b6f1f0612c3fc0007a43ee5e37696b7e48c168；与原scratch文件逐字节比较。未重跑或改写原探针，没有更改.gitattributes、预算或gate。

## 审核绑定

previous-review-evidence.json保存旧canonical完整原字节；provenance-before.json保存当时review/archive原输出和本次实际格式失败。旧reviewed_at/evidence_completed_at、workflow review/archive时间均为历史事实，未倒改。

新canonical更新包装引用、追加本补充证据，并使用本次真实reviewed_at/evidence_completed_at。新增minor finding c2-historical-probe-packaging描述此格式修订；原major重放finding及源码Spec/Quality裁决依据保持。wrapper-check.json保存实际字节/源文件一致性和本次有界格式核对，不表示产品测试重新执行。

原source-index、review-input-state和此前packaging-audit描述的是封装前历史位置与字节，保持原样。该JSON映射解释original_probe.py原位置；不能据其路径变化否认或重写原始执行。新记录只替换当前直接文件引用，不把旧历史快照冒充更新后的库存。

协调者后续应追加一条provenance amendment，指明旧canonical SHA、旧archive时间、本次JSON封装原因和新canonical SHA及实际validator结果；不得改写原review-report/history/state的原时间来声称本次修订已在旧archive时存在。该补充不授权发行、Root晋级或真实宿主资格。
