# 设计与边界

## 决策

- 复用四个既有有界 LRU：matcher contract、phase contract、relationship
  contract、Skill frontmatter。以读取的不可变内容作为解析缓存身份；schema
  内容同样参与。摘要使用同次读取字节，避免校验后再读取不同版本。优先沿用
  `model.py` 的 bytes-key 方式，不添加旁路缓存模块或长期状态。
- campaign 结果在现有准入点按语义严格校验类型：安全布尔、有限非负耗时/费用，
  保留合法缺失值和实际运行错误记录；不改变 grader 或通过标准。
- 用现有局部否定和 action/topic 选择机制修复具体意图边界。保持肯定动作、
  独立子句和权限 IR；不引入大模型判断或任意提升写权限。
  明确动作短语的排序复用 manifest `phrase_classes`，增加可选
  `requested_action` 类并更新原 manifest schema，旧 manifest 仍可校验；
  该 schema 原本不在 packaged schema registry，既有12项 mirror 检查不变，
  不增加第二路由表、IR版本、权限字段或新 schema 文件。优先级仅对本次
  实际肯定命中的动作生效，否定、概念说明和按 ADR 实施不提升文档写作。
  对独立 IR-2/IR-3，复用共同的局部 action 匹配与全出现位置语义；创建
  动词后的限定修饰语仍受同子句否定约束，被解释/审查的动作对象不作为
  当前执行请求。task-mode 与 routing 必须消费同一边界，同时保留后续
  真正肯定动作，不因全句含“解释”就排除实施。在现有 matcher/kernel
  职责内消除重复私有匹配，不增加平行分类器或改权限定义。
  如内核达到原 30KB 上限，将只由 canonical matcher 消费的纯输出格式化
  逻辑归回既有 matcher 格式化入口；先核所有调用点并保持输出逐字段一致，
  不新增 support 模块或调高预算。
- 在现有 context-engineering / context-compress-handoff（必要时 token
  governance）中压缩冗余后加入 active Skill 的来源/内容身份/必要引用与有效
  上下文状态。恢复先核当前目标/权限，再按需加载；同内容完整有效时才去重。
  这是方法指导，不声称 ADK 提供生产 context manager。
- 全量审查和外部比较使用简洁逐项记录，复用既有证据格式和原始日志。
  不复制历史大文件或增加第二套发布/评测/安装体系。

## 职责与文件归属

协调者负责需求/设计/任务、集成与发布；实施者依据本合同修改代码。
core 实施者负责四处缓存、campaign 结果类型及对应测试；routing 实施者负责局部否定、matcher
选择规则、manifest 路由和相应 Skill/回归；context 实施者负责上下文三个
现有 Skill、原始来源取舍和最小消费验证。`_matcher_kernel.py` 中 core 只改
frontmatter loader，routing 只改局部否定/选择段，避免相互覆盖。
最终审查由未参与产品实施的独立 AI 完成，不以自审代替。

## 验证与性能

先保留基线反例，再验证修复。缓存用同路径/相同 size/恢复 mtime 的 contract、
schema 和 frontmatter 变化验证，覆盖错误内容拒绝与有效内容刷新。
路由用正反成对输入和原固定评测；上下文用最小任务输入验证恢复取舍。
重复相同无模型工作负载观察缓存命中与耗时；只报告实际工具耗时，不推导
模型费用。共享代码和 manifest 变更按原规则执行完整回归。

## 回滚与未知项

无公共格式迁移、持久化数据迁移或设备写入。正常受保护 revert 可恢复 11.3.14
源码与前一不可变发布；不覆盖历史 tag、Release、失败记录或资格证据。
初始 PATH 没有 `rtk`；后找到前轮真实 `rtk 1.2.0` 工具，后续 shell 经其官方
proxy 入口。验证使用本轮隔离 Python 3.12 venv；不安装 Agent 运行时。
`knowledge/L2-domain/lessons.md` 不存在，检索结果已记录；不补造历史经验。
历史 hosted ADC/CMake 15 秒等待原因未定，不通过提高超时或反复重试掩盖。
