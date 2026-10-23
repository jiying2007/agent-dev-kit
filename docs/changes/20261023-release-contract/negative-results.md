# 负结果与修复前反例

## 历史来源检查

- `knowledge/L2-domain/lessons.md` 在当前仓库不存在，未声称命中历史经验。
- 调用点已检索 release/distribution、delivery CLI、CI、promotion、archive/strict-JSON/upgrade 测试。不会重新引入 retired release wrapper 或绕过现有发布来源合同。

## 修复前行为回归

命令：`rtk bypass env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src <venv>/bin/python -m unittest discover -s tests -p test_release_integrity.py -v`。

2026-10-23 首次运行退出 1，12 个测试用例耗时 18.062 秒，16 个失败子项、1 个错误。主要观察：

- ignored 哨兵进入合格发布包，source count 从 1532 增加到 1533。
- `assume-unchanged` 隐藏 README 漂移使工作树版本检查失败，说明构建仍读取可变工作目录。
- publish 计划第三资产位置是 `--verify-tag`，没有 `release-contract.json`。
- source 内容、数量、source manifest、重复成员、特殊类型及路径漂移没有被 canonical verifier 拒绝。
- 改名版本在规范版本校验之前进入源 manifest 装载，错误来自 fixture 的完整源缺失，证明公开入口没有首先复用 canonical artifact 版本检查。

正向控制通过：最小真实 source inventory、显式 dirty 开发构建保持不合格、Git attributes 当时尚未用于构建、tracked symlink 已被旧拷贝入口拒绝。没有执行真实 GitHub 发布或模型调用。
