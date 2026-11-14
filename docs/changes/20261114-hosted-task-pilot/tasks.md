# 任务

- [x] H1 冻结独立宿主合同和前次负结果；verify：requirements/design明确source、模型、预算、身份、一次触发和效果边界，保留本地0-run记录。
- [x] H2 实现最小工作流和typed core中的有界实验协调模块及合同测试；verify：官方资产摘要、基线/候选导出、相同输入、模型/镜像预冻结、断网条件隔离、300秒中断与收尾、严格证据allowlist全部显式实现；前置workflow有独立timeout和保守bootstrap回执。修订后的17项定向测试、原失败product-maturity门禁、严格类型及Ruff/格式检查通过；两个实现模块字节和已通过module-size检查的版本相同，不新增产品CLI或manifest入口。原生资格留待H4实际预检；新版本完整回归与最终审查由H3单独判定。
- [x] H3 独立Spec/Quality审查、定向验证和完整回归；verify：C2/b881526的17项定向测试、严格类型与静态检查、完整回归102/102通过；独立Spec/Quality均pass，open blocker/major为0。31个归档成员及11份回执由独立只读审查核验，typed review-evidence实际校验pass。原C的101/102与requires-changes保留；synthetic fixture修复不修改scanner或拒绝语义。此勾选为后续状态记录，C2原tasks快照仍在original.patch/source-bindings中；原生Docker资格仍必须在job实际取得。
- [x] H4 精确源码一次触发并关闭该尝试；verify：run43614661952正常push，before=B/c57、head=C2/b881526、attempt=1，终态failure；模型准备成功后因清单链接被拒，两条件均not-run，93文件原件保留；失败没有重跑。后续回执提交不是执行目标，完成此项不表示原生任务通过。
- [ ] H5 真实任务独立验收尚未运行；verify：独立原始工件审查完成并确认0次任务推理、两侧work仍是初始字节；没有实际任务产物，因此既有grader未调用，实际加载/session/usage仍not-run，不能标为任务验收完成。
- [x] H6 保存已发生结果并更新原计划；verify：result.md、准确原始ZIP和独立工件审查保留完整负结果；原计划记录一次失败和未完成项，后续兼容性修复单独登记，不自动赋予发布/产品/泛化资格。
