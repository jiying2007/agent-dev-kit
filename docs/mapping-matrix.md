# Capability Matrix

下表记录 `agent-dev-kit` 内部能力与实现映射，不依赖外部仓库上下文。

| 能力域 | 目标 | 实现入口 |
|---|---|---|
| 资产安装 | 按工具与 profile 安装 Agents/Skills | `scripts/install_assets.sh`、`scripts/devkit.sh install` |
| 可选技能注入 | 按需安装 optional skills，不影响默认 profile | `optional-skills/`、`scripts/install_assets.sh --with-optional-skill` |
| 资产转换 | 导出多目标目录结构与元数据 | `scripts/convert_assets.sh`、`scripts/devkit.sh convert` |
| 目录索引 | 生成 Agent/Skill/Profile 可检索目录 | `scripts/catalog_assets.sh`、`scripts/devkit.sh catalog` |
| 触发判定 | 输入文本与 skill 触发矩阵匹配 | `scripts/skill_match.sh`、`tests/test_skill_trigger_matrix.sh` |
| 结构校验 | 校验 manifest、frontmatter、profile 关系 | `scripts/validate_assets.sh`、`scripts/devkit.sh validate --strict` |
| 快速预检 | 本地快速检查 frontmatter 与目录映射 | `scripts/validate_assets.sh --quick` |
| 格式一致性 | 检查 LF、tab、脚本 shebang 与可执行位 | `scripts/check_format.sh` |
| 流程工件化 | 统一 propose/apply/verify/review/archive 交付链 | `scripts/workflow.sh`、`docs/changes/` |
| openspec 桥接 | openspec 与 gdk 变更工件双向迁移（导入/导出） | `scripts/openspec_bridge.sh`、`docs/runbooks/openspec-bridge.md` |
| 阶段流转门禁 | 强制 `proposed->applied->verified->review-passed->archived` 顺序 | `scripts/workflow.sh` |
| 单问题与边界核验 | 单次变更聚焦单问题，并显式声明 Core/Optional 归属 | `proposal.md` 模板、`adk-commit-pr-quality-gate` |
| 评审闭环 | blocker/major/minor 分级并归档前强校验 | `scripts/workflow.sh review`、`review-report.md` |
| 负结果留痕 | 记录被证伪假设与不采用方案 | `negative-results.md`、`adk-systematic-debugging` |
| 回归测试 | 覆盖安装、optional、转换、workflow、catalog、trigger matrix | `tests/run_all.sh` |
| 持续集成 | PR/Push 自动执行验证与回归 | `.github/workflows/ci.yml` |
| 发布打包 | 按 tag 构建 dist 并上传制品 | `.github/workflows/release.yml` |

## 独立性约束

1. `manifest.yaml` 为单一事实源，仓库能力不依赖外部仓库文件。
2. 脚本只读取当前仓库目录，不读取其他仓库路径。
3. 新增能力需同步更新命令文档与测试用例，确保可本地独立运行。
