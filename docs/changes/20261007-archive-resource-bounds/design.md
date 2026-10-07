# 设计与证据

8.0.3 `_safe_regular_member`调用getmembers，74,507字节压缩归档在缺失critical文件被拒绝前已缓存12,000个TarInfo，零载荷亦不受JSON8MiB限制。正式8.0.3实际compressed1,768,446字节，1837members，declared6,184,305字节，最大member87,958、最大name107chars。

方案：读取一次bounded regular compressed snapshot（64MiB），同bytes计算artifact SHA；GzipFile分块解压，经forward-only reader累计128MiB，header请求64KiB/累计metadata8MiB、每member隐藏header链32、PAX键256。seek以64KiB消耗实现而非无预算跳过。最多8192成员、单member32MiB、name4096UTF8字节；critical JSON每份沿用8MiB，三份固定名由schema约束，顺序任意且唯一regular。逐next清除TarInfo缓存，避免global PAX映射逐成员复制后持续保留；读到gzip EOF验证CRC并累计尾部/concat流。

实际extraction先对同一快照完成预算预检，再沿用已有5000member、512char路径、类型/重复/根范围检查，不放宽；extracted JSON读取沿用严格budget。无落盘动作的budget验证与真实解包责任分开。
真实rehearsal在创建workspace前捕获previous/candidate同一snapshot并读取有界regular ASCII checksum（8192bytes），摘要与后续提取同bytes；保留lexical叶path。publish入口复用该验证，dry-run仍返回原声明命令，actual上传从私有TemporaryDirectory内的已验证bytes和重新生成checksum完成，退出清理自身临时目录；不再把可替换input路径传给gh上传。测试mock外部写，实际Main发布由授权工作流另验。

外部设计输入：Python官方tarfile文档说明过滤器不防DoS，并建议限制数量/总大小/单文件及OS资源；gzip文档列出BadGzipFile、EOFError、zlib.error。只使用3.8可用API，不使用3.13 stream参数或3.14默认filter。
https://docs.python.org/3/library/tarfile.html#hints-for-further-verification
https://docs.python.org/3/library/gzip.html
