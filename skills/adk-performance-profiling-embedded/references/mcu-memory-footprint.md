# MCU Flash／RAM／stack 资源实测（按需）

## 基线与测量
冻结芯片布局、链接脚本、toolchain/flags、源/配置/ELF hash、map及上板限制。构建失败记 blocked，不报节省。
同工具链用 size -A、nm --print-size --size-sort、objdump/map及 -fstack-usage .su 核 .text/.rodata/.data/.bss、alignment、Flash初始化副本、DMA/uncached/retention区；stack/heap reserve与RTOS逐任务high-water分开核算。

## 安全优化
授权 scope 内先量化 const/rodata、buffer缩容、成员重排、库/section GC、libc/优化级别变更。不得用共享 static 代替可重入局部数组或随意移动 DMA/cache line、保留区/向量表；核 packed 非对齐风险，保留错误路径与可恢复性。
输出 build identity、scope、before/after section bytes及重复测量、remaining risk；验证功能、latency/jitter、温升/功耗和回滚。无板端证据记 needs-runtime-evidence。

## KWS资产复用
核可信清单、实际摘要、来源/许可、采样率/声道、特征/量化版本及目标 profile；匹配才复用录音/特征/模型/ELF基线和回执，只补缺失产物。摘要变化、不适配或无回执仅使相关资产 stale/unverified，按需重做对应步骤，不无故全量重建。复用输入不证明新准确率/资源/时延；仍须同口径实测，区分合成/host与真实录音/板端数据。

## KWS／音频推理比较（按需）
先固定标签、录音划分、噪声条件、采样/分帧/特征配置、量化校准来源、模型与阈值。同一录音及派生片段不得跨训练/验证/测试集；按项目目标隔离说话人或采集场景。验证集选择阈值，冻结测试集作最终比较，不反复用测试集调参。

剪辑分类报告目标类别与 unknown/silence 的混淆；连续监听冻结各候选在验证集确定的阈值/后处理，用一致的误唤醒预算或项目工作点比较误唤醒次数和负音频时长、漏检及触发延迟，不强求不同分数尺度采用同一数值阈值，也不能用剪辑准确率替代流式效果。前端、量化和后处理用共享输入核对 host/target 输出，注明容差；再测板端 Flash/RAM、时延和功耗。仅有合成特征或 host 数据时保留实际覆盖范围，不启动未授权训练/模型服务来补结果。

参考：https://sourceware.org/binutils/docs/binutils/size.html ; https://gcc.gnu.org/onlinedocs/gcc/Developer-Options.html ; https://www.tensorflow.org/datasets/catalog/speech_commands
