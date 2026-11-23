# 产测诊断和放行裁定

保持 `evidence.json` 原样。以其中的证据为唯一输入生成 `readiness.json`，使用以下字段和取值。

- `candidate` 和 `host_diagnostics` 为字符串，分别取输入的候选固件 ID 和 Host 诊断状态。
- `current_board_verification` 为字符串，只接受 `passed`、`failed` 或 `missing`。只有固件 ID 等于当前候选的板测回执才可用于判断。没有匹配回执时填 `missing`。
- `factory_calibration` 为字符串，保留输入的校准状态，未知时填 `unknown`。
- `release_authorized` 为布尔值。当前板测、校准或责任人决定缺失时填 `false`。
- `missing_evidence` 为字符串数组。按设备、校准、责任人顺序填入缺项，ID 分别为 `matching-board-receipt`、`verified-calibration`、`owner-decision`。
