# Manifest 查询边界收敛

- 直接消费 `manifest.json` 的治理/Skill 查询脚本不得接受重复 JSON 键或 NaN/Infinity。
- 查询器不得读取符号链接、非普通文件或超过 16 MiB 的输入；大数据回归（超过 8 MiB 的受控 fixture）仍应成功。
- 使用已有 `strict_json` 内核，不新建解析器、兼容配置或 Manifest 镜像。
- 与开发依赖维护合并为一次受保护版本晋级，后续 Root 只消费不可变发行；不得宣称真实 Runtime 或效果测试通过。
