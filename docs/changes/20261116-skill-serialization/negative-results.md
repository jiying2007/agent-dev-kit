# 负结果与证据边界

- Build 前按 `security|serializ|scan` 检索 `knowledge/L2-domain/lessons.md`，该文件不存在（rg exit 2）；没有借用或伪造历史教训。
- 本轮初始外部对照发现 Addy 的 owner-negative 路由与行为评测完整性建议已在 ADK 有对应检查，保留现有实现；不为重复方法增加规则。
- 初始只读查询不存在的 `references/details.md` 及 `manifests/content_architecture.json` 返回未找到；随后使用实际现有 `skill-scan-coverage.md` 和仓库索引定位，不因此修改合同。
- 既有 v11.3.10 的独立 source/packaging review 和 PR CI 可以复用为其交付证据，不作为本轮新增修改的测试结果。
- 新方法测试在未修复内容上实际执行：3 个测试出现 4 个失败（无发布示例和两个目标缺条件导航），exit 1；修复后同一入口 3/3 通过，详见 `evidence/implementation/{red,green}-published-method.json`。
- 实现者曾向 `check-token-budget.sh` 传入不支持的 `--profile`，exit 2；读取实际 help 后改用原 `--summary-json`，预算通过。错误命令和后续实际结果分别保留，没有修改脚本、阈值或测试来消除失败。
