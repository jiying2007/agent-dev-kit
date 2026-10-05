# 设计

在 `validate_repository` 的 `strict and not quick` 分支追加 `version_identity_failures(root)` 的结果，与已有 governance failures 一起形成现有 v2 summary 的 failures/status。保持原始诊断文本，复用同一 projection SSOT 与版本读取逻辑；不新增平行 checker 或 summary 字段。

回归从真实 `scripts/devkit.sh validate` 消费者入口执行，复制源码到临时 fixture，从非仓库 cwd 启动。分别改变或移除两个原先未被 strict 检测到的 projection，验证 strict 返回码、status 和精确失败原因，同时验证 quick 与 strict+quick。每次恢复 fixture 内容，正式源码 projection 不变。

复制保留 symlink，但 projection 的修改和恢复必须先 unlink 临时副本路径，再创建普通文件，避免沿链接写回原始 target。两个投影的回归均先链接到 fixture 外的临时 target，断言修改及恢复后 target 字节不变、副本 projection 已成为普通文件；所有链接与 target 都只位于临时测试目录。

每个 projection 在读取或修改前验证父目录解析后仍位于 fixture 内，拒绝父目录 symlink 指向外部。回归另创建指向 fixture 外临时目录的父目录链接，确认读取/替换均被拒绝且 target 内容不变，避免 unlink 通过父目录链接影响外部文件。

回滚：移除 strict 分支中的复用调用、导入及对应消费者回归，恢复之前 strict 范围；release 身份检查始终保留。

追加 file-mode 修正：无显式 inventory 时，先把 requested root 规范为 physical root，再用 `git rev-parse --show-toplevel` 读取、规范 Git root 并要求二者相等；替代仅检查 `.git` 目录。inventory 分支不依赖 Git、禁止 `--fix` 的规则以及 index mode 判定均不变。

回归在 TMP 内建立普通 Git 仓和真实 linked worktree，使用 command-local author、禁止签名/用户 hooks 和前台 maintenance 的 synthetic commit；所有 Git 元数据与临时 refs 都在 TMP。从非仓库 cwd 验证调用，覆盖 worktree mode drift、`--fix`、tracked deletion，以及非仓/父仓借用/坏 gitfile 拒绝。Git fixture 调用清空 ambient `ADK_FILE_MODE_INVENTORY`，默认真实源码调用保留 ambient inventory，以兼容 Docker 的无 Git snapshot 边界。回滚只恢复追加的 checker/test/doc 变更，不影响前轮 strict 实现。
