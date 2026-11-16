# 11.3.7 最终独立平台验收

**结论：PASS。源码已合并，v11.3.7 不可变 Release 已发布，当前 main 与 latest Release 身份一致。首次 Release 超时的根因仍未知。** 审阅时间：2026-11-16T03:49:43.844739+00:00。本审阅者仅执行读取、证据核对和隔离取证，没有修改源码、tag、门禁、发布对象或执行重试。

## 源码、CI 与发布身份

| 阶段 | 实际对象与结果 |
|---|---|
| 原冻结源码 | `e90ffe27be645c343ee73762b709238e2e13713a`；38 文件的原 SHA256 在当前发布主线及本地工作区仍一致 |
| 交付映射 | 本地6a → 同树mirror82e → bridge ec2；原bundle已在只有baseline的隔离仓恢复原提交与38文件，bridge仅加入映射与bundle |
| PR 273 | 已合并；精确head ec2，测试merge3a与发布树一致；PR CI43796895613 attempt1，102/102组；9检查成功、两项PR条件skip |
| main | `5f442723e95fa7ca846b7c3ddc9f9995c7a27065`，tree `4c416f50a4d52bb67925e0cbc5d818f7afdc7f1a` |
| main CI | 43797901327 attempt1 completed/success；102/102组；contract、regression、static-security、deterministic-eval-package、promotion-evidence五任务全部实际成功 |
| Release工作流 | 43798551346 attempt2 completed/success，updated_at 03:45:40Z；成功package job133075611855 |
| Tag | v11.3.7，注释对象`6447cb4bd25c1d7436d080455516d854b14b821f`始终peel到同一5f；tagger03:30:21Z，unsigned |
| Release | [446583342](https://github.com/jiying2007/agent-dev-kit/releases/tag/v11.3.7)，draft=false、prerelease=false、immutable=true；published_at 03:44:11Z，latest为同一对象 |

末尾 discover-orphaned-releases 已成功。其实际JSON为 repairs=[]、failures=[]，因此 repair-orphaned-release 按非零repair_count条件合法skip，整个workflow已结束成功。latest-attempt列表中的promotion成功日志仍保留03:30原创建时间；没有把job ID变化解释为二次retag，注释tag对象本身始终相同。

## 保留第一次失败，限定复验结论

| Attempt | Package job | 实际结果 | 完整独立日志 |
|---|---:|---|---|
| 1 | 133073038045 | Validate and smoke失败，61组60 pass/1 fail | 93109B，SHA256 `c4d11a7c058c736bc44234df9720dd277dd76ea6b4ecf256b7dc0ef249c965bf` |
| 2 | 133075611855 | 全部发布步骤成功，61组61 pass/0 fail | 103708B，SHA256 `90c2578ad3089e60a2317bdf130e61311bb5949e3f027af1b9008c0b2d075afe` |

两份独立日志都与root原件逐字节一致。第一次是ADC严格C90方法耗尽未改动的15秒整体预算；配置/构建已返回，最后可见为尝试CTest。没有现场阶段时钟、可检查JUnit或进程状态，不能断言CTest运行了15秒、从未启动、ADC死锁或runner抖动。第二次是原计划限定的唯一普通复验，源码、tag、参数、预算及门禁不变；其成功说明该次完整发布链完成，**不说明超时原因被修复**。

另一路只读诊断未找到确定性ADC错误或前置污染：main与失败Release标称镜像相同，full/quick前四组和content调用相同；存在setup差异但未建立因果联系。唯一一次本地Make探针0.394s通过，只表明该本地环境未复现，不能反证hosted Ninja失败。首次失败与两份独立诊断均原样保留。

五个原来本地缺Ninja的方法已由完整unittest执行链、CI缺工具hard-fail及实际content组通过支持成功完成的推断。compact日志没有逐方法成功回执；空集与compile-only分别验证预期失败和不运行CTest，不被解释为目标测试执行，更不提升为板端/HIL认证。

## 发布资产与独立核验边界

| 资产 | GitHub ID | 字节数 | GitHub SHA256 |
|---|---:|---:|---|
| agent-dev-kit-11.3.7.tar.gz | 753336296 | 5774977 | `01c9f94558ec2ca8676e58718277fa87c49414167f5623f975687fd3eeac5265` |
| agent-dev-kit-11.3.7.tar.gz.sha256 | 753336300 | 94 | `5125697756090dd7aece9bd906bd9d9e9e4c302a4f82d65ff78a725a4190af7e` |
| release-contract.json | 753336297 | 592 | `b5e6e7bc10d6129340d0914f0900a2c3eb4e0f4589e8cc4cddf4abe32be9bf78` |

独立读取GitHub元数据确认三个资产均uploaded，集合、ID、大小和digest与CI输出一致。成功日志实际记录：

- exact-main复用为true，run_id=43797901327；实际checkout仍为5f。
- smoke汇总在03:43:57Z完成61/61；之后archive build、manifest/SBOM/source合同、完整bundle校验、attestation、上传、发布全部成功。
- CI release-contract的status和release_eligible通过，版本11.3.7，archive SHA与GitHub tar资产digest一致；checksum命令实际输出OK。
- 03:44:12Z实际输出`GitHub Release immutable asset digests verified: v11.3.7`，不是脚本中尚未执行的echo。

CI打印的完整contract JSON加原末尾换行可还原592B，SHA256与GitHub contract资产metadata相同，已另存以便复核。这属于CI文本与平台摘要交叉核对，**没有独立下载5.8MB tar或重算其二进制摘要**；也没有由本审阅者独立执行cryptographic attestation verification。unsigned tag与CI provenance步骤成功分别报告，不混称为GPG签名。

## 最终工作区与剩余边界

独立核对本地隔离工作区HEAD/origin-main均5f、tree4c、tag6447→5f、工作树干净、38文件无变化；原feat交付引用6a仍存在。root的final-publication-receipt及final-workspace与这些结果一致。

本次最终平台验收没有剩余发布阻塞；首次超时原因作为未解决问题保留。源码字节、静态方法/任务观察、CI发布资格和真实模型/设备效果继续分开：未运行外部模型A/B，未证明Token/成本/成功率提升，未做ARM/HIL/真实设备认证。四项消费任务仍是一轮新会话的四次定性观察。
