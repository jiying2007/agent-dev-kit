# ADC 构建等待：一次隔离诊断需求

## 目标与实证

定位 exact source `0a6bf985de5e2d3523cd4e82cb19d3b8575a4fdb` / tree `77dcf4a3f0bdd08f9572329c7c2ef1de8f276ca1` 的 ADC 构建等待。PR #284 和 main CI 44139131010 的 full 均102/102；发行44140561472/package134242045032复用main后quick60/61，原ADC用例work15.014s超时，cleanup0.012s/session-unverified。原日志99948B，SHA256 `f49ee3845742cca529f1f625d24685ac1fe11557b6ce9205dbce02a06a74491a`。现有四批快照全部采于TimeoutExpired后且按PID保留较新值，不能说明超时前ar的状态。等待根因仍UNKNOWN。

## 冻结边界

- 一次独立branch push、attempt 1、一个诊断job；分支`diagnose/adc-archive-wait-20261118`。不是旧CI或Release重试；不创建PR、不合入main、不更新tag/Release/Root。
- 原tracked产品、测试、helper、技能、配置、CI和版本字节保持；只新增driver、专用workflow和本change的requirements/design/tasks三文档。
- 仅执行一次`tests/test_skill_content.sh`中原unittest模块及参数序列。driver是明确披露的等价unittest入口；不冒充字节相同的shell调用或完整release环境。原测试文本、排序、失败、skip和退出码均保留。
- 只为原ADC测试实例的`# cmake-build:`调用附加只读观察。原15秒工作时限、1秒cleanup及原清理行为不变；不放宽任何产品/发布门禁。
- 预注册相对真实Popen返回的0.25、2、7、14秒四点；只采当时仍在运行的调用，提前结束的点为NOT_OBSERVED，不补点、不循环至失败或成功。
- 每个样本独立记录读前/后时刻、阶段、PID/SID/start_ticks身份及缺测；owned发现复用原helper的独立scan_state及50ms/256/16上限。只读有限schedstat、io、status白名单、wchan和pipe身份；不读argv、environ、内存，不扫描无关session的FD。
- 归属发现允许原helper有界枚举/proc目录并读取候选stat来筛SID；不输出foreign记录，不读取foreign的附加统计或FD。不能把这称为完全没有读过foreign stat。附加采样与发现共享本样本50ms截止，未采字段保持UNKNOWN；阻塞读导致超时亦如实记录。
- 工具版本/hash在测试结束后采，事前仅path/stat；原件与支持度如实保留。诊断成功不证明历史根因解决，采样扰动和环境差异都必须披露。

## 验收

1. 独立审查确认新增路径与最小权限、确切旧源绑定、测试选择/exit保持、观察边界、四点上限和无资格声明。
2. 本地只做新driver语法/Ruff及隔离synthetic控制；不重跑ADC、skill_content、full或旧远端run。
3. 审查后仅一次远端实验；保留原日志/结果、工具身份、源before/after和Artifact API/实际字节摘要。根因与后续改动必须由新事实决定。

## 不在范围

不升级或固定另一套CMake/Ninja/GCC，不改生成器/并行度/超时，不建立通用observer框架。无secrets、id-token、发布写权限；无模型调用、宿主/设备/M5资格。
