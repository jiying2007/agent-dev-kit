# 持久化与锁输入契约需求

8.0.1之后/tmp实证：campaign固定json.tmp预置链接覆盖外部文件，写出NaN后strict reader拒绝；真实release build返回pass但checksum固定临时链接覆盖外部文件；TargetLock接受NaN超时、非法pid导致非契约TypeError。

验收集中一个持久化安全包：抽取平台中立atomic_io共享exclusive random temporary/fd写入flush/fsync关闭replace；producer同strict reader对象/bytes/depth/finite预算并先于目录修改；campaign/lock regular descriptor输入，正常schema/CLI保留。finite timeout0..300/type与metadata强校验，权限不足不判owner死亡；故障恢复/旧temporary无关数据保持。安装/campaign/lock默认POSIX0600，public checksum0644。

所有实验和测试不用真实模型；source/CI/真实SDK发行/consumer/source-to-live以及owner/M5/产品资格分别验收。Root原参考目录、CodeX本地修改/config/profile受保护，不伪造既有资格缺项。
