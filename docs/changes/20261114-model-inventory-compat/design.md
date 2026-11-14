# 设计

设计者为 `ai/root`；实现者为 `ai/root/consumer_adoption_audit`；独立只读审查者为 `ai/root/task_protocol_audit`。实现者新增具名内部模块 `src/agent_dev_kit/hosted_model_inventory.py`，修改host协调器的模型清单调用及定向测试；不修改native通用清单、发布器、本设计或工作流。

在typed core内新增模型专用清单函数或等价最小职责单元，替换host协调器中唯一的模型数据清单调用。通用inventory、工具清单及发布器保持既有边界。读取已停止准备容器的只读候选数据时先列举并核对目录/文件类型，再解析限定位置的相对链接，逐层拒绝链接祖先；不使用不受约束的resolve-follow和递归目录链接。清单条数有固定上限，JSON/manifest等小型身份文件读取有字节上限；大模型blob用流式摘要。每个允许的链接必须指向同root内直接普通文件，清单同时保存链接本身和目标身份，目标不得脱离原模型集合。被链接manifest与API完整digest绑定；官方布局若还要求其他身份约束，一并按准确源码落实。

固定版本官方 [manifest/manifest.go](https://github.com/ollama/ollama/blob/v0.40.16/manifest/manifest.go) 的Linux写入流程将manifest内容存入content-addressed blob，以相对符号链接建立v2规范命名入口，旧目录入口可能被删除。因此不能继续要求摘要只能出现在 `manifests/` 下；[manifest/paths.go](https://github.com/ollama/ollama/blob/v0.40.16/manifest/paths.go) 定义v2规范主机为ollama.com。[server/model_list.go](https://github.com/ollama/ollama/blob/v0.40.16/server/model_list.go) 的manifest-list分支返回所选child digest；它可能与命名入口所指parent list内容SHA不同。新函数显式绑定选定模型名和规范命名入口，分别支持普通manifest的直接摘要绑定，以及命名parent list→唯一明确child descriptor→内容摘要已核验的leaf→API digest/runner的绑定链。只存在任意同digest blob不能通过；不模拟Go序列化来制造digest，不将parent/child摘要混为一谈。未实现的嵌套、inline或歧义list保持拒绝并说明原因；必须有API digest不匹配、错误命名入口和歧义child的负例。

新模块只接受模型专用输入，边界尽量小，全部异常在推理前失败。调用关系为host→模型清单模块，不增加产品CLI、manifest注册或共享schema。模块体积与依赖数量按仓库现有门禁验证，不为本次修复添加例外。

首次草稿预审实际发现：只对raw链接字符串做词法归一化，会把内核解析为ELOOP或ENOTDIR的路径错误准入。链接目标必须与官方writer产生的规范相对表达严格相等；不能先经过tag、普通文件或其他目录，再用`..`抵消。该草稿Major的独立RED保存在`evidence/cyclic-raw-link-red.json`；后续测试验证真实内核错误与算法拒绝，而不跟随恶意目标取证。JSON解析复用既有`strict_json.loads`并显式限制1MiB与32层，保留重复键、非有限数及UTF-8拒绝。定向回归位于新增`tests/test_hosted_model_inventory.py`，与原`test_hosted_task_pilot.py`共同执行；本次不改已经执行过的工作流。

原始run只证明出现了指定路径的链接，未发布模型存储实体和原始链接目标。合成回归必须明确来自官方实现的最小布局，不能标为重放完整原宿主树。与官方布局不符或尚无法确认的情况保持拒绝。

测试先保留原C2对允许官方布局的失败，再验证允许布局、普通旧布局及不同恶意/异常链接失败。运行受影响合同、类型/静态/module-size检查及仓库要求的完整回归；如最小修复触及模块体积要求，做职责清晰的拆分，不扩张质量门禁例外。

后续源码验证仅说明本地确定性修复成立。此次不启动Docker/模型、没有第二个条件对照，也不把修复后单元结果回写为run43614661952成功。未来真实验证必须另有明确预注册；本轮只保存修复、准确限制与完成回执。
