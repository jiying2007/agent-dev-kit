# 历史发行补发保留 latest：需求

## 问题与证据

用户已授权完成两仓全部优化、受保护发行及消费。方法规范发行的实际工作流 [44211407809](https://github.com/jiying2007/agent-dev-kit/actions/runs/44211407809) 先于 2026-11-18T00:58:32Z 成功发布不可变 `v11.4.3`，随后于 01:07:40Z 补发 `v11.4.2`。01:09:31Z 核验 GitHub `releases/latest` 返回 `v11.4.2`，与当前源码版本不符。具体证据和失败边界见 `negative-results.md`。

## 验收

1. 当前发行必须绑定可信触发 workflow run 及其 exact source，通过原 CI 权限校验后显式允许更新 latest。
2. 历史补发仍核验自身 source 的成功 main CI、执行原全量回归和资产检查；创建时显式禁止更新 latest。
3. 缺失、非法或身份不一致的 latest 控制必须拒绝；原伪造 CI、错误 SHA 等负例继续生效。
4. 在既有测试入口执行真实 workflow 校验和发布命令，验证当前版本创建后历史版本补发不会回退 latest。
5. 经独立 Spec/Quality 审查、原 PR/main CI 后发布不可变 `11.4.4`；核验 latest 与当前 source 对齐，再沿原 helper 和消费 CI 更新 Root。

## 适用与边界

本改动适用于既有受保护 main 发行及其历史补发。已有 release 的重入分支继续验证资产，不承诺重写其 latest 元数据；本次通过新版本正常发布恢复 latest。不扩展为跨工作流的并发排序协议，不新增权限、工作流、schema、发布资产或模型调用。源码、发行、消费、宿主和产品资格仍分别判定。
