# 有限的归档方法对照

## 实施

CLI：`python tools/diagnostics/archive_selection_20261118.py --out <外部fresh绝对目录>`。新job仅精确branch push、contents:read、persist-credentials:false、attempt1拒绝、10分钟上限，固定既有actions；安装strace仅为本实验，不升级编译器/CMake/Ninja。记录实际版本与文件身份，不推定与旧runner相同。

先验证源差异仅五新增路径及原基线不变。选择实际cc，读取其GNU major选择匹配gcc-ar-<major>/gcc-ranlib-<major>；不回退到不匹配wrapper。编译原examples/embedded-test-matrix/src/adc_scale.c，保持-pedantic-errors/-O3/-DNDEBUG/-std=c11与include；共享对象固定basename adc_scale.c.o。两arm在私有目录创建同名libadc_scale.a，以qc再ranlib操作，原对象不得变化；不另加D或LTO选项，保留实际archive头部差异。测试consumer用原tests/test_adc_scale.c及strict c90编译，以显式完整路径链接各自archive，保留真实程序结果，避免-l搜索混用。

四个ar/ranlib分别由strace -f -e trace=openat执行，不用daemonize选项；trace输出仅暂存到该实验私有目录；解析上限1MiB，超出或终止都标不完整，完整原stream摘要按块读取计算。保存过滤后的openat记录及完整原stream摘要/尺寸，原stream不进入artifact；不隐藏过滤/解析/失败数量。白名单为系统库/plugin/loader cache路径及本实验已知路径，其他只计数，不保存路径或原行。成功fd与negative errno分离；输出语义仅所观察的openat。strace只包目标归档工具，外层固定shell依次调用两次strace，共享每组15s/1s的既有helper；第一命令非零时不隐式执行补偿命令，第二命令记NOT_RUN。不能确认超时清理时停止后继组及consumer，防止遗留进程干扰。归档器、编译/链接/consumer均通过有界既有helper运行；不执行任意输入shell。

工具--version/hash在实验后采，事前仅路径/stat及必须的GNU版本选择。产物/输出固定白名单，fresh目录拒绝路径不得写入；诊断错误与真实命令结果区分，源before/after和每条命令身份单独绑定。工具方法不同，若底层ar身份不能直接绑定，仅作整个方法的观测差异，不归因单个--plugin参数。

必要的纯解析/输出拒绝控制可以单独验证；仅允许一次真实本地固定输入结构验证。小型合成控制可验证strace子进程覆盖、退出码保持与超时清理，不重跑产品ADC unittest或suite。固定实验完成后不追加同源成功尝试。

## 判断

确认通用方法实际多打开某些系统plugin/library、匹配方法的成功openat集合不同且同对象归档/consumer一致时，才支持后继“匹配编译器归档工具”方案。即便如此，也不能把历史所有15s等待判为已根治。没有trace或不完整时只保留positive observations，缺记录不证明缺装载。顺序与缓存使耗时比较不具有对照因果效力。

## 来源

- [GNU ar plugin选项](https://www.sourceware.org/binutils/docs/binutils.html)
- [CMake3.31 COMPILER_AR](https://cmake.org/cmake/help/v3.31/variable/CMAKE_LANG_COMPILER_AR.html)
- [CMake3.31 COMPILER_RANLIB](https://cmake.org/cmake/help/v3.31/variable/CMAKE_LANG_COMPILER_RANLIB.html)
- [GCC compiler wrappers](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)

文档只支持机制，当前运行事实以本次原件为准。
