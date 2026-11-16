# 外部来源筛选与采用决定

本轮通过互联网检索与官方仓库内容检查做广泛候选发现，再以 ADK 的具体反例决定采用。成功取得 55 条记录，按仓库 + commit + 路径或官方网页 URL 去重为 **54 个独立文件/页面**：19 个固定 commit 仓库的 48 个文件，另有 6 个官方网页。完整读取 30 项，定向读取 24 项；许可文件也包含在这个统计中。不能把“抓取完整 bytes”写成“全文阅读”，也不能声称穷尽全网。

逐文件 URL、完整 commit、SHA256、实际阅读段落、许可观察及未采用原因在 `evidence/{core,embedded,optional,platform,portfolio}-audit.json`。一个 Aspire `LICENSE` 请求返回 404，随后实际找到 `LICENSE.TXT`；原失败保留。所有第三方内容仅用作方法核验，未安装执行上游脚本，未将其正文复制成 ADK 新资产。

## 固定版本仓库

| 仓库 | 固定 commit | 本轮重点与决定 |
|---|---|---|
| [Agent Skills](https://github.com/agentskills/agentskills) | `83021e2be457a9b6679148719c1f6074f0ad975e` | 格式、按需加载与客户端边界；保留现有 portable projection，不把运行时权限/发现职责搬进编译器 |
| [Vercel Skills](https://github.com/vercel-labs/skills) | `af860243b8c68053b3b5151e3732b9322933674d` | 仅核 Lock File Content Hash 段与许可；已有源身份/产物摘要分层，不引入第二 CLI/lock |
| [Sentry Skills](https://github.com/getsentry/skills) | `a582c51ee29d0f35e6ac321340796f77d43da733` | agents-md、PR writer 的范围与交付；现有边界可保留 |
| [Trail of Bits Skills](https://github.com/trailofbits/skills) | `149d7b21f4067765b82e67029730b42d228ef4b4` | 变体分析/评测及供应链审计；以可执行反例核现有方法，采纳 F1 内容输出边界 |
| [HashiCorp Agent Skills](https://github.com/hashicorp/agent-skills) | `5e30fa5c867ba6777c37e4206babfd08049c396f` | Terraform test 定向段；不为不同领域新建重复 Skill |
| [Microsoft Skills](https://github.com/microsoft/skills) | `f03ec5392f7a0f3aca12af47477e92f1edf7b44c` | Skill creator 指定段的渐进披露/评测；保持现有验证与按需资源，不搬入整套流程 |
| [Vercel Agent Browser](https://github.com/vercel-labs/agent-browser) | `53384771fbafc261ba67608ac806dd5aa70b84f0` | 评测方法；不自动执行其付费模型/native runner |
| [JSON Schema](https://github.com/json-schema-org/website) | `8877a30594da239f86dc1746b3d30abe126a2eb7` | object 中组合/闭合及方言段落支撑 F4 |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | `5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c` | 输出与脱敏方法；F1 修发布命令，不新增安装依赖 |
| [Aspire](https://github.com/microsoft/aspire) | `334b86dd6bde8d14dc971bdfda8df3f9812af935` | flaky test 定向段；保留有限采样，F2 处理当前已确认中断状态 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | `4ed06ed0ddc523a6d356a4ad35ddfea331041888` | Skill best practices；已有触发/窄职责/按需说明可保留 |
| [Kitware CMake](https://github.com/Kitware/CMake) | `859ca5c4d7396a011a462878179bc173e1283731` | compiler/toolchain 文档及真实加载源码支撑 F3 |
| [Embedded Review](https://github.com/ylongw/embedded-review) | `bb500aa00fc3e548365305b537b211663323a3d9` | 嵌入式审查；不把多 reviewer 一致意见当真实设备证据 |
| [Low Level Dev Skills](https://github.com/mohitmishra786/low-level-dev-skills) | `d0d0a13d4e3caec7afb2d647a1fffdb7cb1ee058` | CMake/DMA 方法；保留 ADK 资源预算和证据约束，不引入不受限并发 |
| [Zephyr Agent Skills](https://github.com/beriberikix/zephyr-agent-skills) | `ed63cdfb8cdfbeb5946ea39c33f4aa6bcf3a5cce` | 构建与板端边界；不安装 Docker/执行刷写 |
| [Espressif Skills](https://github.com/espressif/skills) | `ab44d6e1e34260b16de228aea1aa24169cbae53b` | 发现入口，无可直接采用的完整 Skill；不冒充已完成实质评测 |
| [Espressif ESP-DL](https://github.com/espressif/esp-dl) | `512ed0b0dc5f5320f3d9ca5a5aea189803f87f31` | operator Skill 定向段；不把硬件/算子资格映射为通用源码通过 |
| [Zephyr](https://github.com/zephyrproject-rtos/zephyr) | `64e98eb5278d790f3b3e5279ca8b39b45097bbc0` | workqueue/cancel 相关段；现有 RTOS owner/终止边界保留 |
| [Linux](https://github.com/torvalds/linux) | `7d0a66e4bb9081d75c82ec4957c50034cb0ea449` | DMAEngine client 相关段；不将 host 示例视为 DMA 硬件行为 |

## 官方网页

GNU Bash 的 [Exit Status](https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html) 与 [Signals](https://www.gnu.org/software/bash/manual/html_node/Signals.html) 核对子进程状态边界；[RFC 9051](https://www.rfc-editor.org/rfc/rfc9051) 核对只读 IMAP 方法；[RFC 9309](https://www.rfc-editor.org/rfc/rfc9309) 与 [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) 核对 URL 获取方法；[Google SRE Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) 核对已有 RCA 证据方法。网页保留获取时原 bytes 的 SHA256，无法提供 immutable Git revision 的页面明确如此；RFC 按编号固定。

## 平台与许可判断

ADK 内部扩展字段由现有 target renderer 投影或放进命名空间，未未经处理复制到 portable 顶层。基线实际 portable audit 检查 65 个 Skills 为 pass；这只证明源格式/投影契约，不证明客户端发现、加载或触发。Agent Skills 的客户端指南不能授权更宽的目录扫描、工具权限、宽松 YAML 或上下文保留策略。

各来源许可观察分别保留，方法核验不等于已获代码重分发批准。未将 CC-BY-SA、GPL、GFDL 或其他来源正文装入产品；新增说明和合成执行例均为本轮针对 ADK 问题的实现。没有声称“安装越多更优”，没有按热度自动批准第三方能力。
