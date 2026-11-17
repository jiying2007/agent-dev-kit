# 一次性诊断设计

## 执行与身份

专用workflow仅在精确诊断分支push触发，contents:read，checkout不保留凭据，固定现有actions SHA，Ubuntu24.04/Python3.12及与发行相同的安装命令。显式拒绝run_attempt非1；job最多10分钟，artifact always上传但不产生发布或质量资格。镜像实际版本由job日志记录，不宣称与失败runner相同。

run_attempt guard仅拒绝同run的重跑；再次push会形成另一个attempt1。因此本次交付只创建一次已独立审查的分支头，不后续push换SHA取样。原其他push workflows仅main，新workflow名不触发release-tag-promotion。observer仍可能竞争CPU/GIL并改变procfs/cache；本实验不是无扰动对照。

driver CLI为`python tools/diagnostics/adc_wait_20261118.py --out <外部绝对目录>`。启动时核base固定0a6bf985、原tracked输入字节不变、差异仅五个预注册新增路径、输出不在仓库内且不覆盖已有证据。源码before/after与实际诊断HEAD/tree分别记录。PYTHONPATH沿原shell为src，入口补repo root以保持原-m unittest导入语义。

读取原test_skill_content.sh，shlex解析且严格接受唯一python3 -m unittest语句，保留模块列表和-v；使用标准unittest runner/result包装。仅在目标ADC test instance上临时包装published：选定ADC cmake-build后包真实Popen以获得SID/leader身份；其他实例、命令、method和结果不变。published finally恢复所有临时hook，停止observer，在fixture自动清理之前读取限定生成物。异常和unittest失败不转换成成功。

## 观察

observer只调用保留的原owned_process_snapshot，使用独立scan_state并关闭游标；不发送信号、不改communicate/deadline或原cleanup。原snapshot入口可加薄事件hook以标记cleanup开始，observer直接调用原函数避免自触发。记录4个时点的scheduled/actual和采样区间；每个PID的附加字段读取前后核PID/SID/start_ticks一致。竞态、权限/文件缺失、截断和晚点明确标记，不填零或推断complete。

原helper的全局fallback允许有界读取候选/proc stat以判断SID；foreign不得进入输出或附加统计/FD读取。发现与附加字段共享样本50ms截止，read最多4096B且在各读前检查余量；有界是尽力边界，实际超出必须记录，不把阻塞读包装为严格实时保证。

字段白名单：stat既有身份/状态/CPU；schedstat三计数；io计数；status中的信号mask/上下文切换；wchan。每次读取最多4096B。最多16个owned进程，每PID最多64FD；FD只记录pipe inode及访问flags，不保存regular路径或内容，不追无关进程。系统pressure和CLK_TCK仅聚合/解释信息，不能单独归因负载。各字段不是原子快照。

fixture产物仅CMakeCache允许名单工具路径、.ninja_log最多64KiB且保留truncation、已知object/archive/test executable的size/mtime等元数据。工具的resolved path/stat事前取得；--version与二进制hash只在本次测试结束后采，并核stat前后漂移。工具命令仍有独立短时限，失败/不可用保留。禁止整个环境、整个CMakeCache、argv、内存、任意文件内容转储。

## 解释与停止条件

原15秒失败与observer结果独立；四个点只帮助区分调度等待、I/O/pipe等待、CPU活动等假设，不能单独证明根因。一次成功仅说明此诊断运行成功。若没有新证据则保持UNKNOWN，不自动再跑。只有具体证据支持的实质修复才能建立后继源码候选；旧tag与所有失败不可改写。

字段解释依据：[Linux per-process schedstat](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html)与[Linux procfs](https://docs.kernel.org/filesystems/proc.html)。schedstat的运行/运行队列等待计数需同身份差分，io和pressure各有统计口径；缺字段、零值或单一指标均不单独证明根因。
