# 编译器归档工具选择：单次结构对照

## 新事实与假设

前一次预注册诊断44145782657/attempt1已完成，不重复。exact0a6源码的ADC调用11.9602s通过；同ar身份在2→7s均D/folio_wait_bit_common，read_bytes增长65,433,600B而CPU仅36.64ms、runqueue等待0.0967ms。.ninja_log归档edge10331ms，对象1272B、archive1422B。cache实际为ar/ranlib通用工具，另已有gcc-ar-13/gcc-ranlib-13匹配工具。它支持调查大规模页读取，不识别所读文件，也不是历史timeout根因证明。

GNU ar一手文档说明未指定plugin时会在bfd-plugins搜索；CMake的COMPILER_AR/RANLIB wrapper加编译器适用plugin。当前候选解释是通用归档器探测不相关工具链插件，但必须先取证，不能先断言LLVM装载或旧timeout原因。

Build前经验检索：本基线没有knowledge/L2-domain/lessons.md，已记录负结果；本次差异是由前一固定run的新I/O事实转向文件打开集合，既有失败和已关闭实验不重试。

## 固定实验

- 基线0a6bf985de5e2d3523cd4e82cb19d3b8575a4fdb/tree77dcf4a3f0bdd08f9572329c7c2ef1de8f276ca1，原tracked inputs不变；精确新增driver、专用workflow、三合同共五文件。
- 新分支diagnose/adc-archive-selection-20261118只创建一次head，一个attempt1 job；不是之前branch/run/release重试，没有PR、主线、tag、Root或资格写入。
- 一次编译原ADC C11源为固定小object，同一原字节与member basename用于两个独立新archive。固定顺序为通用ar/ranlib，再compiler-matched gcc-ar/gcc-ranlib，各命令只执行一次。
- 每个归档命令单独用strace只观察openat；不trace外层shell、compiler、link或consumer，不采集进程argv/environ、不跟踪execve参数、不转储任意内存或文件内容。strace会解码syscall参数，不能宣称完全不读tracee参数内存。保留成功open与ENOENT区别、解析失败/过滤/截断和trace完整性；只保存系统library/plugin及本实验已知构建路径的过滤记录。
- 每组ar→ranlib共用一次原run_example的15s work/1s cleanup，阶段间不重置预算；原helper和测试文本不改。固定最多一次编译、两组归档、两次显式archive链接和两次consumer执行，共七次有界helper调用，另有必要工具身份查询。一个arm失败仍保留，清理完整时另一个按既定计划执行一次；清理无法确认则停止后继组并记录NOT_RUN，不重试任一命令或至成功才停。
- 两个archive都完成时核同object摘要、archive原字节摘要/大小、各自用原C90 consumer链接并实际运行原断言。不同环境的结果各自标记；不把本实验当原ADC/unittest/Release资格。
- 观察目标严格为成功openat文件集合及产物语义差异；打开不等于成功dlopen/mmap，未见openat不等于没有其他文件访问。固定顺序有缓存混杂，禁止以耗时差宣称性能因果或回填旧失败。

## 验收与停止

本地允许一次新driver结构/功能验证（不是原ADC test或suite重跑），保留实际source/tool/exit与输出；然后独立审查固定候选，远端最多一次。任何额外源变更或后继修复都要独立事实、设计与审查，不自动追加实验。旧UNKNOWN与全部失败不可改写。

## 实际本地能力边界（执行前补充）

2026-11-17T18:42:53Z的单次/bin/true窄探针actual exit1，PTRACE_TRACEME/PTRACE_SETOPTIONS均报Operation not permitted，raw trace为0B；stderr为283B、SHA256为54c4fd1054c5c741ab0218ea148520f87ad3298ea3fac32a7fbfe043550ca21f，与先前两项真实strace控制的早退错误一致。stderr只保存长度/摘要及窄探针的错误token，没有完整原始字节，不能声称逐字审核了三份原stderr，也不回构或补跑。两项控制保留FAIL；它们未进入预期子进程/cleanup阶段，不能证明跟踪或清理成功。本地ADC结构实验明确NOT_RUN_CAPABILITY_BLOCKED，未编译ADC，不追加提权、策略修改、替代trace或重试。

本地纯逻辑/AST/Ruff结果与上述能力失败分开保留，不能替代实际编译器/归档对照。独立审查仅可判断固定driver是否足以进行原已登记的一次hosted观察；该次观察仍自行承担真实trace、产物和consumer验收，不增加remote次数，也不授予产品测试或发行资格。
