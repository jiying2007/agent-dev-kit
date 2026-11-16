# 三项工程判断

请按各自 ADK Skill 使用以下任务样例，给同事一份可直接采用的处理意见。只分析已有材料，不访问设备、不运行网络采集、不修改源仓。

## A. 寄存器适配

待交付寄存器表有两行：

| 地址 | 权限 | 任务给定的手册内容 | 现有观察 |
|---|---|---|---|
| 0x100 | read-only，读取无副作用 | POR 后低4位为3，高4位 undefined；该字段只在 POR 约束 | POR 后读回0xA3；软件复位后读回0xB0 |
| 0x104 | FIFO read-clear | POR 后数值 undefined；读操作出队 | 尚未读取 |

请完成复位表说明、判断现有观察能支持什么结论，并给必要的下一步。另有0x108寄存器尚未查到手册说明。

## B. 协议适配

应用协议为两个字节大端长度加 payload，长度上限4096。stream端记录如下：第一次recv返回1字节00；第二次返回8字节0361626300026465；第三次返回0。datagram端一个独立请求收到了合法空报文，后续仍收到 `next`；另一次recvmsg缓冲容量4，返回`ABCD`且flags含MSG_TRUNC，之后可读检查没有后续数据。

请说明应交付的完整payload、EOF与datagram的区别、截断如何处理，以及发送端单次write只写出前3字节时的处理。现有实现每次read到新字节就重设30秒总超时。

## C. 测量判断

同事说“测试通过且candidate目录中的libengine.so哈希更新，所以可以把性能变化归因于新kernel”。已留证据：benchmark ELF哈希未变；本次进程maps显示 `/opt/baseline/libengine.so`；文件系统上 `/opt/candidate/libengine.so` 是新哈希；测试报告pass=12。没有kernel或dispatch trace。只能分析这些材料，不启动其他进程或改库。

请给结论、证据缺口和最小下一步，不编造性能数字。
