# 设计

删除 `unlock` 帮助、函数及分支，版本升级仍同步权威身份。档案脚本在 dispatch 中，仅对 restore/rollback 使用 `lib-python-runtime.sh`，先验证解释器，随后才进入任何写入；恢复仍调用既有 typed core。

复用 `test_python_launcher.sh` 的隔离锁负例及 `test_archive_restore.py` 的真实目标无副作用测试，不增加新框架、兼容入口或额外工作流。
