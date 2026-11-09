# 实施验证清单

- [x] 修复不闭合 Markdown 代码块，加入所有登记 Skill 的结构性反例测试
- [x] 增强深模块/接口设计、领域反例、TDD、调试反馈回路、纵向任务拆分和可抛弃原型
- [x] 在现有可选 Skill 创建治理里建立 RED→GREEN 行为评价要求与 `not-measured` 边界
- [x] 提供源级回归案例及盲评协议，禁止假称模型层效果
- [ ] 主线发布元数据、Profile 源字节保护线按精确变更同步
- [ ] GitHub 11.2.0 PR 完整回归、保护合并、合并后 CI、不可变 Release
- [ ] Root 使用真实 Sigstore 晋级并完成受保护集成；实际 native 行为需独立证据

验证入口：`bash scripts/devkit.sh validate --strict`、`python -m unittest tests.test_skill_content_contract -v`、`bash tests/run_all.sh`。
