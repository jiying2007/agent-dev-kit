# CI修复验证

原失败HEAD：`b9f250adf8fc4bc8d35dff2e5b2d44376a5e8dc9`。
原始CI日志提取见 `evidence/ci-failures.json`；字段/时间保留工具返回，不补造执行。

- GitHub原HEAD的完整regression于2026-11-14T12:43:01Z输出 `tests=102 pass=102 fail=0`。
  contract与static-security另有失败；deterministic-eval-package只运行前置要求检查即失败，其余全部skipped，未执行包评估。
- 实现者按CI清单、正确MYPYPATH和全新cache重现14错，最小修复后32个入口source通过。
  协调者于2026-11-14T12:46:24Z前以同样完整清单/新cache实际复验通过；不是仅四个新模块的定向检查。
- 实现者运行agent_value 19项、agent_value_trust 7项、effect_trials 35项、run_evidence 5+22+15项，均通过。
  新增负例覆盖无效/缺失/混合Agent ID与三种各自缺失的聚合时间；不放宽原验证。
- 独立审查者以只读 `-B` 执行两个新增负例及两个有效控制，4/4通过。
- 原失败日志4512字节无损编码为JSON；反编码与真实Git对象 `c1ccff:原路径` 完全相同，
  SHA-256为 `1e7224bf9148123949774cc7be27eff343ef4b4c640c5331222b45c7133836bf`。
- 临时Git index纳入所有待提交改动后 against `ebef1106` 的完整diff格式检查为0；module-size/fan-out政策通过，未增加support模块。

上述记录不意味着修复后最终HEAD的完整CI已运行；该门禁在新提交上独立检查。
旧源码审查记录仍保留原字节和时间，其适用的证据提交为 `b9f250ad`，
原记录SHA为 `569732ed76186e632f4b324842e026114d812aa956dcf3c06f40c8688a794d9b`。
当前树格式和日志容器已改变，旧记录不能在当前路径冒充fresh pass；重建历史记录需使用原Git对象。
本增量记录独立绑定 `b9f250ad -> 修复源码提交`，不会更改旧时间或复制新的计量/发布权威。
