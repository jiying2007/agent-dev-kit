# Driver Bring-up Runbook

## 适用场景

- 新外设初次上板
- 驱动与中断/DMA/时钟/复位路径首次联调

## 推荐 Agent 链

`requirements-analyst -> driver-engineer -> component-engineer -> test-validation-engineer`

## 推荐 Skill 组合

- `gdk-register-map-design`
- `gdk-driver-bringup-checklist`
- `gdk-interrupt-dma-patterns`
- `gdk-toolchain-debug-openocd-gdb`
- `gdk-integration-hil-sil`
- `gdk-systematic-debugging`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "新增外设 bring-up"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <change-id>
```

## 验收门禁

- bring-up checklist 至少覆盖时钟、复位、中断、DMA
- 联调日志可复现（关键寄存器读写/中断计数/吞吐结果）
- `verify-report.md` 包含 HIL/SIL 或等效板级验证证据
- `negative-results.md` 记录被证伪假设，避免重复排障
- 评审报告中 blocker/major 必须为 0
