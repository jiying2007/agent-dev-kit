# 源码验证：20261118-owned-build-session

## 固定身份与适用边界

基线 `15fa31d1a3f994a516d5a9003edaadd1295c74b5`；实现 `22c2dc2b6d398e49afee675f339040ff612a271e`；最终受测产品 `5ff076a14c88c65132e44dd8bfdb4c2ab71ee4f8`、tree `14e5482c9ea3f97abe6abfcc74f8251088e46e8e`。变化为一个既有测试文件和九个版本/变更日志投影；版本11.4.1。最终helper SHA256 `a17791efaf2ad0dd7b0923dc49b4c219df0a3eb563495b419cc9de281cb12fc0`。

完整验证在精确提交的洁净detached worktree执行；工具venv在工作树外，实际CPython3.12.14。1082个运行源输入前后逐文件一致，HEAD/tree和tracked clean不变。后续change证据、review/archive是另行审查的包装，不冒称在该次full内已有。原main两轮失败在@negative-results.md和@evidence/baseline/index.json保留，旧run无attempt3。

## 实际验证结果

| 层级 | 命令或观察 | 结果 | 原件 |
|---|---|---|---|
| 定向RED | 原helper执行固定真实Ninja新验收 | exit1；漏采leaf、返回complete后leaf仍活两项失败 | evidence/implementation/red-ninja/result.json.json |
| 定向RED | 首版修复后的晚期状态读取异常 | exit1；诊断异常覆盖timeout，随后修复 | evidence/implementation/red-late-status/result.json.json |
| 定向最终 | `python -m unittest tests.test_skill_command_examples -v` | 52/52、0skip；含11项runner及原ADC/CMake | evidence/implementation/green-module-final/result.json.json |
| 定向最终 | `python -m ruff check tests/test_skill_command_examples.py` | exit0 | evidence/implementation/ruff-final/result.json.json |
| 静态/契约 | Ruff、focused Ruff、mypy32文件、format、strict、release-check、core export | 7阶段exit0；export5 agents/22 skills | evidence/full/results.json.json |
| 完整回归 | `bash tests/run_all.sh --timing-json ...` | 102/102、exit0；timing389541ms，实际进程389.665338884s | evidence/full/full-timing.json.json |
| 独立窄复验 | 原0.2s Ninja probe原字节运行一次 | 原oracle期待旧缺陷，实际exit1/not-confirmed如实保留；快照含新PGID后代，返回后无live后代，补杀次数0 | evidence/independent/original-counterexample/ninja-cleanup-probe-result.json.json |
| 独立负控制 | 实际pidfd、伪SID/变starttime、缺pidfd能力 | 独立harness exit0；拒绝外会话和漂移，控制进程存活；缺能力保持unverified | evidence/independent/probe-result.json.json |
| 生命周期verify | strict、format、change-governance | 实际exit0 | verify-report.md |

full实际UTC为`2026-11-17T16:19:07.115768Z`至`16:25:36.781098Z`，source-after完成于`16:25:36.837638Z`。原full日志SHA256 `0d1bee4e82001511f12291d9c3be0867228a5a396f58b49d3acd176ef3eed61e`。所有原结果以可逆JSON包装保留字节、长度、摘要和原exit；完整清单见@evidence/implementation/index.json、@evidence/full/index.json、@evidence/independent/index.json。

## 尚未被上述证据证明的事项

历史hosted ADC/CMake的15秒等待原因仍UNKNOWN；修复发生于timeout之后的观测/清理分支，不能把本地或后续新head通过反推为原等待根治。实际work预算15秒、cleanup总期限1秒、诊断50ms/256entries/16records保持。主动另建SID的任意逃逸不是此helper保证。

format保留既有非可执行shell脚本warning，结果仍exit0；release-check中runtime_eval_executed=false。未执行付费模型、live宿主安装、设备或M5资格。本阶段新PR/main CI、受保护合并、不可变Release及Root source-only晋级仍须各自真实回执；最终独立Spec/Quality以真实review-evidence.json为准，不在此预认证。
