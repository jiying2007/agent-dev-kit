# MCU Flash／RAM／stack 资源实测优化（按需）

## 锁定基线
记录芯片内存布局、链接脚本、工具链、CFLAGS/LDFLAGS、源/配置/ELF hash、map 和上板限制。先完成成功构建；不能构建则标 blocked，禁止从代码直觉报告“已节省 N 字节”。

## 实测维度
按目标 toolchain 使用 size -A、nm --print-size --size-sort、objdump 与 linker map；需要时检查 -fstack-usage 的 .su。分别记录 .text/.rodata/.data/.bss、stack/heap reserve、alignment、Flash 初始化副本、DMA/uncached/retention 区域。对 RTOS 还要按任务核算栈和 high-water，不仅看一个主栈。

## 安全优化
- const/rodata、buffer 缩容、成员重排、冗余库函数、section GC、libc/优化级别变更都要先量化；只修改用户授权 scope。
- 不能仅为节省 stack 把可重入函数局部数组改为共享 static；不随意移动 DMA、cache line、保留区和向量表。
- packed 可能带来非对齐异常；新优化不能删错误路径、扩大不可恢复风险。
- 除字节变化，还要证明功能等价、实时 latency/jitter、温升/功耗与回滚。

输出：build identity、scope、before/after section bytes、repeated measurement、timing/behavior tests、remaining risk。没有目标板证据时 needs-runtime-evidence。

参考：https://sourceware.org/binutils/docs/binutils/size.html ; https://gcc.gnu.org/onlinedocs/gcc/Developer-Options.html
