# 真实失败记录

- PR265 HEAD b9f250ad：contract-py3.12失败，四个新文档EOF空行和first-integration.txt的两行尾空白。
  本地check-format时这些材料尚未tracked，未覆盖最终提交diff；后续核最终Git对象的完整差异。
- 同HEAD static-security的完整strict mypy失败：五个既有模块共14错误；新task入口代码的四文件定向检查不能替代完整依赖图。
- 在新cache下，仅PYTHONPATH包含src的本地完整清单仍可静默跳过导入错误；显式五模块和MYPYPATH解析用于等价复现。
- 首轮集成诊断的101/102日志有真实空白，保留全部原字节于JSON，不通过删失败或改返回码修格式。
