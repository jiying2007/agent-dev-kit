# 测试波动 — 按需取证

沿用 `../SKILL.md` 的风险、权限、统计与隔离边界。重复次数只限定 smoke，不证明低失败率目标；不执行未经审查的测试或生产操作。

## 先定义样本与结果

- 从测试框架的 JUnit/JSON/原生报告读取精确用例 ID、每次结果和执行环境；空格、方括号等属于名称，不作为正则或 shell 分词。日志命中次数不是失败数，进程非零也不等于所有用例失败。
- 分开记录 `passed / failed / error / skipped / missing`。分母来自真正执行的用例或同一用例的独立运行次数；报告计划次数、实际次数和排除原因。缺报告、收集/启动错误或全部跳过不能算成功样本，更不能从分母静默删除不利结果。
- 只有逐轮报告完整、版本/选择器/环境可比，才计算用例失败率并说明统计假设；无法归因时只报告原退出码与未知项。框架已有统计工具优先，不用通用 grep 推算。

## 有界命令采样（Bash）

从项目已核测试入口构造 `test_command` 数组，再调用 `run_flaky_samples 10 <新证据目录> "${test_command[@]}"`。命令自身须有适用的超时/取消路径；次数限制不限制单次耗时。每次 `FLAKY_SAMPLE_DIR` 指向新目录，已审查的项目 runner 可用它保存 JUnit/JSON；不支持时仅取得日志和退出码，不宣称用例报告完整。没有 eval，不执行日志里的命令。

```bash
run_flaky_samples() (
  set -euo pipefail
  (( $# >= 3 )) || { printf 'usage: run_flaky_samples <1-20> <new-directory> <command> [args...]\n' >&2; exit 2; }
  samples=$1
  evidence=$2
  shift 2
  [[ "$samples" =~ ^([1-9]|1[0-9]|20)$ ]] || exit 2
  mkdir -- "$evidence" || exit 2
  evidence=$(cd -- "$evidence" && pwd -P) || exit 2
  printf 'attempt\texit_code\n' > "$evidence/results.tsv" || exit 2
  failed=0
  for ((attempt=1; attempt<=samples; attempt++)); do
    sample_dir="$evidence/run-$attempt"
    mkdir -- "$sample_dir" || exit 2
    exec 3>"$sample_dir/output.log" || exit 2
    result=0
    FLAKY_SAMPLE_DIR="$sample_dir" "$@" >&3 2>&1 || result=$?
    exec 3>&- || exit 2
    printf '%s\t%s\n' "$attempt" "$result" >> "$evidence/results.tsv" || exit 2
    if (( result != 0 )); then failed=1; fi
  done
  printf 'attempts=%s\nrecords=%s\n' "$samples" "$evidence/results.tsv" || exit 2
  exit "$failed"
)
```

返回 0 只表示已采样命令均返回 0，仍须核真实报告和选择器；1 表示至少一次非零，2 表示参数或采集失败。任何失败保留目录与已得样本，不 append 旧日志、不重跑到绿；采集失败不得产出完整性/稳定性通过结论。

## 环境比较与最小诊断

独跑与 suite 结果不同或有共享状态线索时，先保存原 runner 的顺序、seed、worker 和进程边界，再比较 victim 独跑、原 suite、可疑前序→victim 与反序；不把本来同进程的场景拆成新进程后宣称复现成功。逐步缩小前序集合，检查全局状态、环境、缓存、时钟和资源残留；多个污染者可能有非单调交互，普通二分不能保证定位。只改变待证伪变量，保留逐例原始报告。新进程全绿不单独证明同进程污染修复；若隔离本身是设计修复，另验证边界、成本与原失败路径。无顺序线索时不强制此矩阵。

先比较版本、已脱敏配置和资源状态。以下仅列相关变量**名称**；需要值时逐项使用已核安全白名单，凭据值不进入日志。

```bash
# environment-names: values are never printed
python3 - <<'PY'
import json, os
print(json.dumps(sorted(name for name in os.environ
                       if any(key in name.upper() for key in ("TEST", "CI", "DEBUG")))))
PY
```

日志检索只定位假设，不作为统计结果：

```bash
rg -n 'timeout|race|port already in use|resource busy|connection refused' <test-log-directory>
```

单次实验记录 `hypothesis / changed variable / expected / observed / raw report / disproved-or-open`。重试方案记录原策略、预算、适用错误和停止条件；隔离记录 owner、原测试状态、解除条件及 CI 证据，不能把 quarantine 计为 PASS。只在证据支持跨层因果时展开 5-Why，验证修复后仍保留原失败与通过路径。
