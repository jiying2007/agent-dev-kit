# 实现设计 / 失败边界

1. Workflow IR：从 Stage Contract 正文解析严格序号和 Stage ID，要求它们与 frontmatter 列表完全一致（包括顺序），再保留既有精确 digest gate。Skill curation 将已存在的 package 正文阶段登记到 frontmatter 与 policy.stage_bindings，类型 design-write 仍须受 scope 约束；不执行真实 package/publish。
2. Driver：Manifest routing 引入独立 driver_implementation primary（workspace-write ceiling 不提升 live-device），收窄 driver_bringup 的触发词；两种 Skill 的独立职责与现场写权限分离。
3. 触发降噪：去掉 production_field_readiness 的泛化“自动推进”，去掉 structured-requirements-questioning 的文档校对/审查伪阳性；保留显式独立原有资格。
4. CI：合同与回归所有支持 Python 的 PR 路径在 apt/pip/全量回归前做当前 SHA 对精确 base manifest 的 SemVer 前进判断。Regression 的 shallow checkout 仅显式 fetch exact BASE_SHA，不信任漂移 main branch。既有 required check 名称和 if: always() 支持版本汇总维持。
5. 测试：补正文多出/漏掉/乱序/重复/错误序号阶段负例；全目录 route/trigger 正负 case；source-version preflight ordering ratchet。

## 来源与回退

- ADK v8.2.0 protected main 22e6c790d1ed191cecc3083dc001a6ccfed264f6；source version 8.2.1 候选，必须另行取得真实独立当前源码 Spec/Quality Harness 七维复审。
- 原源回退为上个不可变组件 Release v8.2.0；运行态/Root pin 仅在新受保护 main CI、Tag Promotion/签名证据成功后按 canonical source promotion 更新。
- 任何失败保留负结果，不能用旧版本审核绑定为新版本发签，不能降低 3.8 支持或假报 Token 降幅。
