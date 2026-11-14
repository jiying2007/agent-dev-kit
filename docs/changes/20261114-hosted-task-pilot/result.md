# 唯一托管尝试的实际结果

## 裁决

Run [43614661952](https://github.com/jiying2007/agent-dev-kit/actions/runs/43614661952)、job `132506978963`、attempt 1执行准确C2 `b8815263a31ee3b004c2e7e9eee564fe8a35dfc8`。它于2026-11-14T16:16:02Z创建，16:17:09Z终态为failure。模型准备成功后，host模型清单因符号链接拒绝而停止；baseline与candidate均为not-run。没有重新触发、rerun、选择性补跑或扩大模型预算。

正式v11.3.1发布与本实验分别判定。本实验没有产生任务效果、Skill实际加载或Token/费用/时延收益，也不满足消费者的真实原生门禁。

## 已观察的准备结果

实际Docker镜像构建、官方工具获取和模型pull成功。qwen3:1.7b的原生`model.json`报告完整digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`，size为1359293444。准备容器ExitCode=0、Running=false、Pid=0，docker rm返回0；Ollama子进程-9对应finally主动停止，不能误算为模型推理失败。

实际错误为`Unexpected symlink in data: .../models/manifests-v2/ollama.com/library/qwen3/1.7b`。此时完整模型文件清单和`frozen-runtime.json`尚未生成；summary保留model_digest unavailable。原生API观察与完整内容冻结不是同一项证据，原summary保持字节不变。模型存储实体及实际readlink目标未发布，不能根据这个工件推定目标合法。

## 条件与验收

| 项目 | baseline | candidate |
| --- | --- | --- |
| OpenCode原生配置/断网容器预检 | not-run | not-run |
| 任务CLI与推理 | not-run | not-run |
| 实际Skill加载/session/export | not-run | not-run |
| usage/任务验收 | not-run | not-run |
| 最终work | 初始379字节ADR未变 | 初始379字节ADR未变 |

`conditions=[]`和0次任务推理由实际命令、原生日志与C2控制流交叉核实。两个work不是模型产物，因此未调用既有grade-task对它们生成假想任务结果。未测Token或费用保持not-run，不填写数值0。

## 工件完整性与独立审查

GitHub [artifact 14121104537](https://github.com/jiying2007/agent-dev-kit/actions/runs/43614661952/artifacts/14121104537) 原始ZIP为63,998 bytes，SHA256 `72d3c3c86939d14ba14a36ef1bb1d2475ec93b0ac5573933833a8dc6161c2f01`。93个成员通过CRC与安全路径检查；91个native manifest成员全部匹配长度、摘要与ZIP原字节，其余恰为manifest和bootstrap。bootstrap独立绑定summary摘要；未误称它受native manifest覆盖。

独立工件审查实际时间为2026-11-14T16:22:26.026203Z；审查原件SHA256为`94d19b1e1ce983cd36eabb6a41a9ad0b153785b955218f7fa5ac97dbb799696f`。未发布模型权重、安装包、私人home、native state/cache或完整仓库。唯一脱敏Ollama日志保存原件摘要与删除行号，审查只核验实际提供的发布副本，没有重建身份行。

交付包包含原始ZIP、GitHub终态/独立API复查、准确job文本、触发回执及两路审查，77,947 bytes，SHA256 `5f4d7aae8359224eee00b08ce2f257a71fa66b68865528fb619bb857cbc07b76`。它是失败准备证据，不是效果认证。

## 后续源码修复

模型清单兼容性修复在`../20261114-model-inventory-compat/`单独登记。它针对固定官方版本的v2链接布局和manifest-list的parent/child摘要语义；不放宽通用inventory或发布allowlist。局部源码验证不回写本次结果，不移动执行分支，也不启动第二次任务。真实任务效果与独立新任务验证仍未完成。
