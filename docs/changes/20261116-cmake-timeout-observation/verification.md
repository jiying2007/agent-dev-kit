# 实现与定向验证

## 实现范围

仅修改 `tests/test_skill_command_examples.py`：

- CMake fixture 的 xtrace 使用 Bash 内建 `EPOCHREALTIME` 时间戳，并设置 `VERBOSE=1`；发布的 Skill 代码块未修改。
- 只在原 `TimeoutExpired` 路径采集当前 `Popen` 所属进程组的 procfs 状态；输出仅含 PID、PGID、comm、state、CPU ticks、wchan，不读取 argv/environ。
- 进程发现最多检查256个目录项、输出16条记录，分配至多50ms检查窗口。所有读取均使用固定长度，并在循环及可选wchan读取前核对截止时间。诊断与原kill/reap共用原有1秒清理截止，不新增工作预算。
- procfs缺失、进程退出、非法记录或诊断异常只影响诊断状态；仍终止自有进程组并报告原始超时。

这是失败观测增强；没有宣称解释或修复历史ADC/CMake超时。

## 实际执行

在 `/workspace/scratch/fe8de3b42084/adk` 执行：

```bash
/workspace/scratch/fe5385ca063a/verification-tools/rtk bypass env \
  PATH=/workspace/scratch/771b38332ec2/domain-audit-tools/cmake-wheel/cmake/data/bin:/workspace/scratch/fe5385ca063a/verification-tools:/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin:/usr/local/bin:/usr/bin:/bin \
  /opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B \
  -m unittest tests.test_skill_command_examples.CommandExampleRunnerTests -v
```

最终定向复验结果：exit 0，5/5通过，0 skips，unittest记录0.616秒。原始输出见 `evidence/runner-tests.txt`。此前首次定向执行同为5/5通过（0.615秒）；整合复读发现繁忙procfs可合法耗尽诊断预算，因此最终版本只在完整observed扫描时要求真实child被观测，bounded/partial不改变原清理断言。可控procfs夹具独立验证数量上限和非本组排除。

验证内容：正常exit 0/7及原15秒默认值；真实慢子进程仍在0.5秒工作预算超时、保留stdout/stderr并被清理；独立进程组保持存活；参数和环境的合成敏感标记不进入诊断；缺procfs、消失/不完整记录及缺wchan不抛新异常；记录条数受限；清理截止已过时不访问procfs；诊断异常不泄漏异常文本、不替换超时或阻止cleanup。`git diff --check` 同次执行通过。

## 尚待整合

原ADC/CMake实例、方法聚合、独立Spec/Quality审查及精确候选CI由parent执行并补充真实回执。这里不把本地定向通过表示为CI恢复、根因结论、Release或Root接入完成。
