# 临时 Git fixture 隔离设计

统一 helper 在每次 Git 子进程调用中移除继承的 GIT_* 环境变量，指定空 global/system 配置、禁用 system 配置读取，并通过 command-local 参数固定身份、关闭签名、hook、GC、maintenance及detach。init 使用专有空 template；保护配置写入合成仓库 local config，避免后续只读身份探针触发维护。只保留非Git环境，不修改父进程 os.environ。

确定性回归同时注入 global/system 配置、运行时配置、template hook、外部 GIT_DIR/GIT_WORK_TREE/index 和非法作者日期。对外部仓库身份、无额外index、无hook标记、fixture单commit及local保护配置作行为断言。隔离修复前该输入实际在commit阶段因非法日期失败；修复后通过。原身份测试保留全部断言。

参考：Git官方配置文档说明 maintenance.auto 控制命令后自动维护，autoDetach 控制后台运行；GIT_CONFIG_*及GIT_DIR可以改变子进程读取的配置和目标仓库。https://git-scm.com/docs/git-config 与 https://git-scm.com/docs/git 。原失败现场只证明TemporaryDirectory退出时.git目录非空，没有具体writer。

风险与回滚：helper只用于测试。回滚本change的单个测试文件及文档即可；无runtime或源版本迁移。禁止忽略cleanup异常、重试删除或杀其他进程。默认Git版本与runner不同，托管矩阵仍需真实结果。
