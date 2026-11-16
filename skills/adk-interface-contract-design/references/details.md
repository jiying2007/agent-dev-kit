# adk-interface-contract-design — 补充参考资料

## 有方向的版本/能力检查

只适用已验证的增量 API 策略：同 major 的新 minor 保留旧能力；本消费者要求 `2.1` 语义与 `ASYNC_CANCEL`。版本/能力来自已验证解码，不能从版本臆造能力。16 位 major/minor 不是完整 SemVer；wire 布局、字节序、ABI、取消/错误语义仍须验证。实际协议不保证向后兼容时改用明确支持矩阵。

```c
#include <stdbool.h>
#include <stdint.h>

/* Inputs to this encoding must be validated components in 0..255. */
#define IFACE_VERSION_MAKE(major, minor) \
    ((uint16_t)(((uint16_t)(major) << 8) | (uint16_t)(minor)))
#define IFACE_CAP_ASYNC_CANCEL (UINT32_C(1) << 0)

bool iface_version_compatible(uint16_t remote_ver, uint32_t remote_caps)
{
    const uint8_t major = (uint8_t)(remote_ver >> 8);
    const uint8_t minor = (uint8_t)(remote_ver & UINT16_C(0xff));
    return major == 2 && minor >= 1 &&
           (remote_caps & IFACE_CAP_ASYNC_CANCEL) == IFACE_CAP_ASYNC_CANCEL;
}
```

带必需能力的 `2.1`/`2.2` 通过本检查；`2.0`、缺能力或跨 major 拒绝。仅报告 `3.0` 不证明支持 `2.x`；本地 `2.1..2.2` 与对端仅 `2.0` 无交集，不能降级。记录双方身份、支持集合来源、选择/拒绝依据与实际验证。

方法依据：[SemVer](https://semver.org/) 的公共 API 承诺与最低功能依赖版本；不把版本号当 wire/ABI 认证。

## Commands
```bash
# 接口定义扫描
rg -n "interface|api|contract|schema" <module_path>
rg -n "typedef.*\(" include/<module>/*.h

# 版本信息检查
rg -n "VERSION|version|COMPAT" include/<module>/

# 废弃接口扫描
rg -n "TODO.*compat|deprecated|DEPRECATED" <module_path>

# 结构体对齐检查（嵌入式关键）
pahole --class_name=iface_msg_t <module>.o

```
契约测试用项目真实入口；host 字节打包示例不能证明目标协议字节序。
