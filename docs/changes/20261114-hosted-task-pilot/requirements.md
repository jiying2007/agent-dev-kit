# 公共 Actions 原生任务先导

## 目标和授权范围

使用已允许的公开 GitHub Actions 执行环境、官方 OpenCode 与免费本地 Ollama，直接运行一个真实开发任务的新旧条件，取得可复核原始记录。此环境执行任务本身，不作为本地网络代理。代码仅保存在实验分支，不修改ADK正式版本、已发布runtime、消费者本地门禁或发布工作流。新增Python协调工具遵守根规则置于typed core，但不注册产品CLI、不更改manifest、不进入正式主线或发布包。

本地先导的 `environment-blocked-before-inference` 与 model_runs=0 保留，证据包SHA256为 `6b5a76779320f45422ca4a06dfa394fff85106d352b65e7fbea56da7aa6018ca`。本次是独立宿主预注册；不能重新标记该历史结果或重置其一次环境修正记录。

## 冻结范围

- 开发任务：`targeted-document-edit`；使用当前正式源码的原始task、initial/work和case合同。执行模型不能读取case、验收答案、整个仓库或来源checkout。
- baseline：11.2.17 / `7aed1d2545babce16c41dc021ead01c8c324ce07`。
- candidate：已发布11.3.1 / `c57f4f8a7983f52257c0587eb85881a006e6dc07`。只导出并暴露各自真实 `adk-adr-writer`，内容摘要和引用集合在运行前冻结。
- 官方完整导出文件身份：baseline SHA256 `e0672708e80c0636abaa812fa6be8d81d7b9f062a62e322b505c7f7d07c4e215`；candidate SHA256 `a21c9d9d2fd3aaf1e759e28c0353139a1fee67c2ea1e790e1fc882a54f0c60d4`。candidate源文件SHA256为`e013d6e67dc993a3c3a0cf589d6e1c1e3b4534c1a053422c8c1df0c04813dba2`，与11.3.0源文件逐字节相同；导出文件因真实版本元数据变化而不同，保留原样，不为匹配旧摘要修改内容。源文件与导出文件身份分别记录。
- OpenCode v2.3.0官方Linux x64归档SHA256：`fc0f81522aceeabac47693d88389efa2bc517ce74c2c38fd6967819fcc6e4d3b`。
- Ollama v0.40.16官方amd64归档SHA256：`87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d`。
- 唯一模型：`qwen3:1.7b`；只在准备阶段下载，在任何推理前冻结真实完整digest，两个条件使用同一只读模型集合。缺digest禁止启动条件。
- 宿主：公开`ubuntu-24.04` runner上的标准Docker。记录实际runner image、Docker版本、官方基础镜像digest、最终容器image ID及依赖清单；全部在推理前冻结，两条件相同。
- 固定顺序baseline后candidate，各一个CLI任务调用，各最多300秒；超时、错误、未加载、失败产物完整保留。不单侧重跑，不改模型、任务或预算筛选成功。

## 执行前输入身份

任务源码身份统一为candidate正式提交`c57f4f8a7983f52257c0587eb85881a006e6dc07`，两个条件使用该提交的同一任务与初始工作区；Skill干预来源分别为上述baseline/candidate提交，二者不与任务源码身份混用。两个选定Skill导出目录各仅有`SKILL.md`，声明的外部参考文件集合均为`[]`；这些准备身份不证明实际加载。

| 对象 | 字节数 | SHA256 |
| --- | ---: | --- |
| baseline源`skills/adk-adr-writer/SKILL.md` | 2614 | `04267d6288de34d97f2774aa016f1c3366f75699a8638d9c57a5875f376dfcc1` |
| candidate源`skills/adk-adr-writer/SKILL.md` | 3680 | `e013d6e67dc993a3c3a0cf589d6e1c1e3b4534c1a053422c8c1df0c04813dba2` |
| `targeted-document-edit/task.md` | 351 | `6bc93366986b29af97fe8328f1c338ae90763a235ba917531b803e8df7e6bc44` |
| `targeted-document-edit/initial/docs/ADR-021.md` | 379 | `6a6249b2f8df6c2a8cbea872f13319dd42cb07779bea6e204bfd614f19144359` |
| 共同prompt | 407 | `5d70cb0689e244f868c32fb92600a3d96a0945fc4724be3d924952a2e8b252db` |
| 执行器外`targeted-document-edit/case.json` | 454 | `a9a6143b2a36c324435c321171ad09925457dd8d7f8209180ff64f1ecebe59e0` |

路径根为`tests/fixtures/skill_execution_tasks/`。prompt严格按以下字节拼接，不trim或重排：

```python
prompt_bytes = task_bytes + "\n请使用 `adk-adr-writer` Skill 完成上述任务。\n".encode("utf-8")
```

ADR中的`docs/protocol-v2.md#retry`仅是需保留的字面引用，fixture未提供引用目标，不临时生成或挂载该文档。运行前核对上述摘要；不匹配即停止。

## 必须满足

1. 先审查源码，再一次性正常push触发。仅exact repository、execution branch、before base SHA及run_attempt=1允许进入；之后的新push或rerun不再进入模型执行。
2. 一个公开job最多30分钟；workflow首步记录实际开始时间，协调执行以该起点26分钟为截止，为收尾、上传及启动开销保留4分钟。冻结成对执行预留为1140秒：两个300秒任务、两个100秒恢复、每个容器70秒外层启动/终止/取证上限，以及60秒记录/拷贝余量。workflow前置checkout/setup-python/pip/定向测试采用各自明确step timeout，总上界300秒；首步时钟步骤另限60秒。它们的实际耗时全额扣入首步起420秒准备预算，但不声称GitHub action自己动态扣费。协调器一进入即按该420秒绝对截止限制后续准备操作，余量不足不启动模型。任何前置失败都由独立的always短时fallback保留真实步骤outcome；execution若曾进入而缺完整回执只能标unknown，不能补造0-run。任一准备前置未完成或启动第一个条件前不再有1140秒余量，两个条件均不启动，不缩短单侧预算或只执行一侧。准备失败即停止，不修改宿主网络/AppArmor/sysctl，不切换隔离机制、不要求额外权限或绕过拒绝。
3. 准备容器可下载公开模型。推理前停止联网准备容器；两个执行容器均`--network none`，只用容器内loopback。不得挂载仓库、case、`.git`、凭据目录或Docker socket。
4. 仅挂载只读官方工具、模型、所选Skill/配置，以及当前条件的work与原生日志目录。HOME/CODEX_HOME不被重定义；镜像中该普通用户原生home路径及必要的`/tmp`使用各容器独立tmpfs，供Ollama临时身份和运行状态使用，不绑定宿主home，不进入证据发布包。无云provider、subagent、联网工具、shell或任务外读写。
5. 无模型的隔离预检先证实只读根、挂载集合、无任务答案/宿主凭据、断外网及本地服务健康。任一关键前置不满足，两个条件均not-run。
6. 完整保存实际命令、版本、起止时间、返回码、session身份及原生日志/可得导出、前后文件摘要。私钥/身份引导行不得进入发布包；脱敏副本必须标注并保留原件摘要。
   任务容器启动前先登记尝试；实际启动之后即使inspect/logs/remove或导出失败，也保留可能已执行的状态和已有原件，不能退回model_runs=0、空条件或not-run。未知执行状态明确为unknown/partial。
7. 使用既有`grade-task`在执行器外独立验收最终工件。没有原始样本前不新建日志转换器；不确定coverage或缺usage不得填true或0。
8. 单任务先导只支持链路诊断及描述性结果，不关闭原方案的独立新任务验证、完整小批诊断或收益门槛，不回填legacy方法campaign。
9. 固定顺序、单次执行及共享宿主文件缓存均为已知限制。两条件原生服务/状态各自全新，但不清理宿主缓存、不声称硬件缓存等价；不将一对耗时或Token差值解释为稳定的因果收益或全量Skills认证。
