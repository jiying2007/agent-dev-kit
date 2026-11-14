# 设计

复用既有官方导出、原任务文件、上一份准备脚本已核实的v2配置结构和官方CLI。本次新增范围仅为实验分支上的一次性工作流与有界实验协调模块，不实现另一套推理循环、scheduler、统计器或生产adapter。

根规则要求新增Python工具归入typed core，不能以“一次性实验”为由制造例外。因此宿主事件/来源、镜像、容器预算及证据协调放在`src/agent_dev_kit/hosted_task_pilot.py`；容器内原生配置、健康检查、任务及官方导出放在`src/agent_dev_kit/hosted_task_native.py`，宿主单向依赖native模块。两模块各自满足现有30KB预算，不新增豁免或通用support模块。容器仅挂载native模块的准确副本，保存源/副本摘要，不挂整个Python包或repo。合同派生测试放在`tests/test_hosted_task_pilot.py`。工作流使用`PYTHONPATH=src python -m agent_dev_kit.hosted_task_pilot`，不新增稳定CLI或manifest入口。`docs/changes/`仅承载需求设计、任务及证据。此源码仅同步到实验分支，不合并主线，不改变现有发布版本。新增隔离与执行工具按安全变更运行一次完整回归，并完成适用静态/类型检查。

执行分支固定为`experiment/hosted-task-pilot-run-20261114`，初始base B为`c57f4f8a7983f52257c0587eb85881a006e6dc07`。源码提交C先放在不触发模型的review branch，经独立只读Spec/Quality审查后，执行分支从B建立，再用expected_sha=B的普通fast-forward update_ref一次前移到C。workflow的exact ref、repository、event.before=B及run_attempt=1共同限制触发；没有workflow_dispatch、schedule或rerun路径。connector拒绝正常workflow/ref权限时停止，不另找凭据通道。

公开runner已提供Docker。固定使用标准容器，不依赖bubblewrap或改变Ubuntu安全设置。官方基础镜像在准备时解析为真实digest；为官方二进制准备必要动态库后封存image ID与包版本。官方工具归档先校验完整SHA再解包；允许根据真实tar目录只保留CPU必需成员，但不修改可执行字节。只读检查可用资源，资源不足按环境阻塞终止，不清理未知runner资产或扩大硬件额度。

workflow首步记录真实时间，实验协调共用26分钟截止，为30分钟job上限保留4分钟收尾/上传余量。成对执行预留1140秒，计算为`2 × (300 + 100 + 2 × 70) + 60`：任务、恢复、四个容器各70秒外层生命周期及60秒记录/拷贝余量。因而checkout/依赖、资产与模型/镜像准备和两侧preflight共用首步起420秒截止。各准备操作timeout随该截止收紧，不能只给子命令独立上限。两个preflight全部结束后且仍有完整1140秒余量，才允许启动第一个条件；不足则两侧not-run。单任务推理上限仍为300秒，恢复上限100秒；实际daemon故障保留partial，不能为弥补开销缩短候选预算。

准备阶段下载同一模型并保存实际digest；无推理预热，不把准备API请求记为模型调用。停止准备容器后再执行baseline/candidate，各自使用全新容器和独立状态目录。使用只读根、能力最小化、无新增权限、有限PID/CPU/内存及network none。官方Ollama与OpenCode在同一容器中通过loopback连接，工具/模型/Skill/config只读。持久可写挂载仅为该条件work及明确原生记录目录；镜像中该普通用户原生home路径和必要的`/tmp`另用各容器独立tmpfs，承接Ollama实际首启写入及运行临时状态，HOME字符串不被覆盖，且不绑定宿主目录、不收集或发布其内容。预检实际验证home可写、跨条件隔离及宿主home不可见。模型不可见case与完整ADK源码。运行前验证挂载与拒绝边界，之后不再改变配置。

外层协调器负责从该条件首次推理前开始计算的300秒预算、实际中断与容器退出确认；预算覆盖该条件全部推理，达到上限立即终止实际执行容器并确认退出，不把Docker客户端结束等同于容器已停止。原生OpenCode负责所有模型与工具行为，官方session导出只读获取。保留失败和缺测；收集范围使用逐文件allowlist，排除home、私钥、token、缓存和二进制/模型。最终work及原始命令、事件、摘要进入Actions artifact，取得后由既有grader独立验收；若在不同job验收，case只存在于grader所在checkout，不进入执行容器。

推理容器停止并确认后，可启动单独的有界恢复容器执行官方session list/export。这一容器无模型挂载、无Ollama服务、无网络，work只读，不执行任务或调用模型；它不能延长推理预算。先保留原生状态的原始摘要，导出若需要可写运行状态则使用明确标注的副本及独立临时区，原记录不得被覆盖；导出失败如实保留，不修造session或usage。恢复临时状态仍排除于发布包之外。

条件尝试在容器启动前登记，之后的inspect、日志、移除、导出等故障不能抹掉先前可能已发生的推理。异常收尾核对现存task-start及容器回执；已启动或无法排除执行的条件保持partial/unknown，不能重新标记0-run或not-run。合同测试注入任务启动后的记录/移除失败以验证保守状态传播，故障注入本身不作为原生Docker通过证据。

协调/需求设计由ai/root负责，workflow/脚本实现由独立执行者承担，Spec/Quality审查由未实现该脚本的只读审查者承担。触发前完成本地可执行的语法、配置、资源/身份/路径拒绝检查；Docker原生隔离的实际资格由job预检取得，不能以静态审查冒充。准备或任务失败均保留，不通过重新push或rerun取代失败。
