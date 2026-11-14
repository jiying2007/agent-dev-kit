# 任务

- [x] H1 冻结独立宿主合同和前次负结果；verify：requirements/design明确source、模型、预算、身份、一次触发和效果边界，保留本地0-run记录。
- [x] H2 实现最小工作流和typed core中的有界实验协调模块及合同测试；verify：官方资产摘要、基线/候选导出、相同输入、模型/镜像预冻结、断网条件隔离、300秒中断与收尾、严格证据allowlist全部显式实现；前置workflow有独立timeout和保守bootstrap回执。修订后的17项定向测试、原失败product-maturity门禁、严格类型及Ruff/格式检查通过；两个实现模块字节和已通过module-size检查的版本相同，不新增产品CLI或manifest入口。原生资格留待H4实际预检；新版本完整回归与最终审查由H3单独判定。
- [x] H3 独立Spec/Quality审查、定向验证和完整回归；verify：C2/b881526的17项定向测试、严格类型与静态检查、完整回归102/102通过；独立Spec/Quality均pass，open blocker/major为0。31个归档成员及11份回执由独立只读审查核验，typed review-evidence实际校验pass。原C的101/102与requires-changes保留；synthetic fixture修复不修改scanner或拒绝语义。此勾选为后续状态记录，C2原tasks快照仍在original.patch/source-bindings中；原生Docker资格仍必须在job实际取得。
- [ ] H4 精确源码一次触发；verify：正常权限允许，before=B/c57、head=C2/b881526、attempt=1；准备记录及两个实际条件结果完整保存；失败不重跑。后续回执提交不是执行目标。
- [ ] H5 独立工件验收和原始证据审查；verify：使用既有grader，区分实际加载/执行/覆盖/usage及unknown，不把成功声明作为外部验收。
- [ ] H6 保存结果并更新原计划；verify：实验身份、全部失败、原始引用、适用范围和剩余未测项清楚，证据不自动赋予发布/产品/泛化资格。
