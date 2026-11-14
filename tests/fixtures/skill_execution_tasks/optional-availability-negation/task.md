# Optional 安装状态与用户否定

这里的 inventory 是宿主提供的可信已安装清单；catalog 命中只是发现，不代表安装。读取三个 requests，输出 `routes.json`（相同顺序），每项 request_id、state、selected、load、install。selected 为 Skill ID 或 null；load 为拟加载 ID 数组；install 必须 false。本任务只制定路由决定，不实际加载或安装。

absent：用户只要求只读吸收方案且禁止安装，所点名 Optional 未安装，state=not-installed，selected=null，load=[]。negated：已安装的 prose 能力被显式排除，state=user-excluded，selected=null，load=[]。available：用户明确允许且确已安装，可选择该 Optional，state=installed-eligible。保留 inventory 和 requests，不得把 planned-load 声称成 native loaded。
