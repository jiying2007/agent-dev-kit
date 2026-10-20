# 设计

## 来源分离

`create_plan`、`validate_plan`、`apply_plan` 新增可选 keyword-only `previous_manifest`；省略时沿用当前 manifest，保持首次安装和同版本重装。CLI 的 plan/apply/rollback 提供 `--previous-source`，只加载操作者显式审查的源码目录。跨版本调用者必须分别提供候选和前版的精确源码。plan 的 active receipt SHA256 继续绑定旧状态，不增加可编辑的来源路径或第二套库存。

`rollback` 保留必填 keyword-only `manifest` 验证当前安装，并新增 `previous_manifest` 验证备份前序 receipt。前序 receipt 的 target/tool、完整 renderer 库存、来源/渲染 digest 必须匹配；每个旧资产都有且只有一个对应备份。备份字节及 mode 由旧源码约束，不能使用新资产 mode 或仅依赖可重写的备份 digest。所有检查完成后才进入现有原子恢复和补偿路径。

## 历史重现边界

内部历史 target loader 与正常 loader 共用结构、日期顺序和最大窗口、native 信任以及布局验证。历史分支只免除 `expires_at < today` 的当前新操作准入条件；不读取 receipt.created_at 作为可信时间、不改变 contract digest、不发出当前认证结果。内部历史 renderer 只供 receipt 库存验证；新 plan/apply/export/check 仍使用默认的当前 loader。

## 演练和迁移

release rehearsal 将已验证解包的 previous/candidate Manifest 分别传给升级、apply 与 rollback，并比较旧 receipt 原始字节、资产字节 hash 和文件 mode。测试使用隔离临时目录中的真实不同版本源码、Git fixture 和 release artifact，不 mock 安装/恢复/来源验证。测试 fixture 不代表正式发布或原生运行证据。

API 全库调用点已检索：生产调用仅在 installation_plan、installation_transaction、delivery_cli、release；其余为 tests。旧的必填 rollback manifest 约束继续保留。升级迁移是在 plan、apply、rollback 都显式给出同一个受审查的旧来源；错误来源 fail closed。回退代码前须先用新实现恢复旧安装，旧代码不支持跨版本安装状态。

旧源码必须仍满足当前 Manifest/target schema 并可被当前受信 renderer 重现；不会动态执行旧源码 Python 或提供任意历史语义迁移。继续恢复已还原的 A 时，新版已安装 CLI 可用既有 `ADK_ROOT` 选择 A 资产源。权限校验函数接受 `object` 类型的 JSON 边界输入后执行原有字符串/八进制和精确权限验证，消除静态类型与运行合同不一致。

## 文档与验证

修正 usage 与 commands 的 Python 3.11 残留，README 将不受支持解释器明确为低于 3.8。测试从 AC1–AC5 派生，接入已有 installer 与 release 回归入口，不引入新的资格 Gate。本地使用已校验的官方 rtk 1.0.1 和隔离 Python 3.12 环境执行定向及全量回归；真实 Python 3.8/3.11 与完整 repo 发布门禁由后续 PR CI 验证。缺少审查 runtime，不能声明 Provider/Execution Policy 已通过。

主任务在现有 `.github/workflows/ci.yml` focused strict mypy 步骤中加入 installation_inventory、installation_plan、installation_transaction、targets、target_contracts、delivery_cli、release 七个模块，不新增 job 或独立 Gate。该调用链已在本地通过同样的严格检查，持续覆盖 rollback 必填参数及来源传递。
