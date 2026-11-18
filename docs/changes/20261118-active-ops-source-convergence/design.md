# 最小变更设计

- 由现有 `agent_dev_kit.versioning` 的同步合同维护 Manifest、pyproject、package __version__、README、CONTEXT、software M5 campaign 和 .version-lock；本次通过 GitHub 源树原子提交相同的受管字段，禁止手动发标签。
- `auto-ops` 保留帮助、命令路由、只读 security scan、低 Token JSON 及 `maintenance_plan` 转发；移除入口永远不可达的写入函数，修正文案为真实只读状态。不得通过 `--apply` 或 `--force` 打开任何旧支路。
- 保留 `scripts/backup-rollback.sh` 作为 ADK 自身受控安装快照能力；只删除已经失效的 Root“完整版”说法。
- 许可证换成 PEP 639 SPDX 字符串；历史 8.0.0 / 9.0.0 迁移记载留存于 `CHANGELOG.md` 和原 change pack，不占当前 README 操作说明。
- 仅补充现有性能/运维测试的负控制；不得新增一个影子维护框架或产品资格台账。
