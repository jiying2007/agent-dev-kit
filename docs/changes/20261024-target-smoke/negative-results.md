# 负向证据

## 修改前真实行为测试

- 基线：`415590db44e88979185efb850e2339a3f95411ef`。
- 新测试从冻结验收条件派生，先在旧 `targets.py` 执行；没有 mock runtime 或改动资格合同。
- 命令：`PYTHONPATH=src python3 -m unittest discover -s tests -p test_target_smoke.py -v`。
- 结果：8 项运行，3 项通过、5 项失败，exit 1，5.826 秒。原始输出见 `evidence/red-target-smoke.txt`。
- 两个真实进程组反例均发现：报告 timeout 后后代仍写 marker（父进程存活和提前退出持 pipe 两种情况）。
- 16 MiB stdout、stdout/stderr 各 600 KiB 的合计超量均被旧入口接受；公共 CLI 对超量返回 0。
- 成功/nonzero 的计数和摘要语义、合计恰好 1 MiB 边界已经通过，后续修复不得破坏。

## 调用点检索

迁移前全库检索 `_kill_process`、`_drain`、`_execute_async`、`_execute`、`native_campaign_execution`、`run_target_smoke`。生产调用点为 `delivery_cli.py` 和 native orchestration；native 测试导入 `_execute` 与 `_semantic_assertion`。保留 native `_execute` 的业务错误映射，不建立兼容 alias；底层执行 owner 下沉为 stdlib-only 共享模块，避免 targets/native 反向依赖。动态外部私有符号使用不属于已声明公共 API。

## 第一版提取暴露的 transport 清理缺口

首次从 native reader/task 实现提取共享 owner 后，8 项 smoke 行为断言通过，但实际运行输出仍出现 `ResourceWarning` 与 `Event loop is closed`。不能把该运行当作无缺陷验证。原始输出见 `evidence/first-pass-with-resource-warnings.txt`。

根因是已退出 launcher 的后代仍持有管道；取消 StreamReader task 并不关闭底层 pipe transport。先补真实独立 Python 进程回归，开启 `ResourceWarning` 并触发垃圾回收，要求 stderr 为空。旧提取实现运行 1 项、失败 1 项、exit 1，1.330 秒；原始输出见 `evidence/red-transport-cleanup.txt`。

随后改用公开 `asyncio.SubprocessProtocol` / `SubprocessTransport` 统一持有进程和管道，在失败时终止进程组、关闭 transport，并等待完整关闭；不访问 `Process._transport` 私有字段。Python 文档明确区分 `process_exited` 与管道关闭，并公开 `SubprocessTransport.close()`：<https://docs.python.org/3/library/asyncio-protocol.html>。

## 范围

探针仅使用隔离临时目录和本地 Python 进程。没有模型调用、Native 认证、现场证据或远端写入。历史 lessons 与 Knowledge Provider 的环境缺口沿用本 change 设计中已记录的事实。

## Python 3.8 的隔离环境负例与同源对照

独立 reviewer 在 CPython 3.8.20 / PyYAML 6.0.3 / jsonschema 4.17.3 的原 smoke 测试观察到 exact-combined-budget 与 live-parent-timeout 两项失败，后者耗时约 6.14 秒；其原始记录保留在独立审查目录。实现者随后对当前 `process_execution.py` SHA-256 `01e3da0bc9cee08055dafafb178c270f8e6ece2a18de2ad542027a1b252d5b9d` 重放同一个 `test_timeout_stops_descendant_before_returning`，在默认隔离执行环境确认失败：elapsed 6.115 秒，原断言要求 <2.75 秒，原始输出见 `evidence/red-python38-sandbox-timeout.txt`。

未改源码、测试、解释器或 deadline，仅通过标准工具的 `require_escalated` 在 host 进程可见性下执行完全相同测试：PASS，整个测试 3.416 秒（包含原测试额外 2.3 秒 marker 等待）。接着同源全部 9 项 smoke 在 host 环境 PASS，9.644 秒，无资源警告；原始输出见 `evidence/green-python38-host-timeout.txt` 和 `evidence/green-python38-host-smoke.txt`。

这构成环境关联反证，不能把隔离环境负例直接归为已确认的产品 Python 3.8 回归。没有增加清理等待、放宽时限或删除断言；独立 reviewer 继续保存 callback lifecycle 对照并作最终同源 host 复验。本记录也不把 host 通过推断为所有隔离运行平台均已验证。

独立 callback trace 随后定位到隔离环境的 `ThreadedChildWatcher` 线程→event-loop 唤醒延迟：exact 1 MiB 用例在约 0.020 秒已经 `waitpid.return` 且两路 pipe lost，但 `process_exited` 直到约 5.007 秒的 timer 唤醒才被处理；host 同脚本在 0.016570 秒 waitpid 返回后，0.016704 秒即处理 process_exited，0.017396 秒完成。live-launcher 超时用例同样已完成 waitpid 回收，只是 callback 再迟约 5.005 秒。故不是没有收割子进程，也不是生产清理等待常量本身有兼容缺陷；不为这一环境事件循环行为增加生产兼容分支。原 trace 保存在独立审核的 `lifecycle-python38-sandbox.json` / `lifecycle-python38-host.json` 中。
