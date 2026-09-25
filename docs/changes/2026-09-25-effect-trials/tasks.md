# 实施检查点

- [x] 复用原子 comparator 和 Run Evidence，不复制权限/receipt authority。
- [x] 固定计划、完整试验集合、全局运行去重和跨条件控制核验。
- [x] 任务级统计、不确定性、可靠性分解和缺失指标语义。
- [x] 增加 compare-trials CLI、输入/输出 schema、packaged mirrors 与 registry。
- [x] 新增确定性负例和合成统计 fixtures。
- [ ] 全仓 Python 3.11/3.12 CI、真实发布与 Root 集成：以关联 PR 的最新运行结果为准。
- [ ] 真实运行时/模型效果实验：没有运行，不声明已测得收益。

本地环境来自 SHA256 已核验的 immutable 7.0.32 release source。rtk 不在本执行环境中，本地直接调用 Python 的结果不冒充 rtk/native 验证。完整 Git 元数据和 GitHub 发布由远端 CI 验证。
## 本地已执行

`python -m unittest discover -s tests -p test_effect_trials.py`：32 tests / OK；来自已核验 release source 的局部执行。未使用模型或provider凭证，不作为真实产品收益证据。