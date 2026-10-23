# 设计：固定源码快照与唯一发布合同

设计者：主 Agent。实现由独立 implement_release 承担，审核与实现身份分离。

## 输入所有权

- release_artifacts 在明确 commit/tree 后，从 Git ls-tree/cat-file 读取固定 blob 创建临时快照；编译、验证、打包都使用该快照 Manifest。
- 不依赖工作目录中的 ignored/untracked 数据，也不依赖 git archive 属性替换后的内容冒充原始 blob。
- 保留显式发布 surface 过滤和权限，拒绝不受支持类型，处理 gitlink/符号链接应沿现有合同明确失败或排除，不能静默提升完整性。
- dirty/unbound 开发构建仍可按既有开发合同输出，并保持 release_eligible=false。

## 产物与发布所有权

- 扩展现有 distribution/archive_io 的有界读取能力，在读取成员时增量收集 source 清单与摘要，不把全归档无界加载或落盘。
- release_contract 校验 source manifest、count/digest 与声明值；保留外层 checksum 校验。
- 公开 publish 复用 canonical validator 与标准完整资产集合；发布使用已验证的字节快照，避免验证与上传之间重新读取漂移。
- workflow 若需调整须先通知主 Agent 串行整合；不自行改 schema/version/CI。

## 迁移与回滚

合法版本与三份标准资产保持；错误命名、缺成员或漂移产物由原先误通过改为拒绝。测试合法 fixture 必须包含真实最小 source。先检索调用点再改公共/内部接口。回滚通过受保护变更，不能修改既有不可变发布。

## 方法吸收

采用输入身份与结果校验分离、公开行为回归、幂等重建和小接口所有权；来源见本轮审查记录，不引入第三方框架。
