# 外部来源与采用范围

本轮采用官方/一手来源。这里只列采用决策，完整来源定位、版本、阅读范围、可用的原文 hash 与检索负结果保存在审计包；没有把背景检索结果都算作采用的新 Skill。

| 来源 | 本轮使用范围 | 决定 |
| --- | --- | --- |
| [Linux 6.12 fault injection](https://kernel.org/doc/html/v6.12/fault-injection/fault-injection.html) | fail-nth 的实际注入与尚未注入区别；函数错误注入前置状态与清理约束 | 将实际命中证据纳入既有故障注入方法；未操作内核注入接口。 |
| [RFC 9051](https://www.rfc-editor.org/rfc/rfc9051.html) §2.3.3、SEARCH/FETCH相关段落 | INTERNALDATE与Date不同；日期搜索忽略时间/时区；BODY.PEEK只读正文获取 | 精确请求使用有覆盖依据的候选与所选时间字段；保留只读合同。 |
| [RFC 3501](https://www.rfc-editor.org/rfc/rfc3501.html#section-6.4.4) | IMAP4rev1对应日期搜索子集 | 确认本地IMAP4rev1夹具使用的子集语义一致，不声称测试完整协议。 |
| [Python 3.12 imaplib](https://docs.python.org/3.12/library/imaplib.html) | IMAP4_stream、UID、FETCH和只读选择接口 | 仅用于host协议夹具；本地解释器实际为3.12.14。 |
| [GNU ld --wrap](https://sourceware.org/binutils/docs/ld/Options.html) | 链接器符号包装 | 仅用于host malloc/free受控探针，非真实设备注入器。 |

嵌入式组还核对 Linux 6.12 DMA、CMSIS-SVD、FreeRTOS Kernel/Kernel Book、Linux recv 相关一手材料；其中部分是前轮已下载的固定来源重新读取并复核 hash，不能说成全新下载。该组本轮6个Skill均KEEP。

未采用：IMAP完整地址精确匹配、尚未定位真实consumer的diagnostic harness关联约定、没有受控新反例支持的其他改写。本次网络查证不等于穷尽全网所有Skill。
