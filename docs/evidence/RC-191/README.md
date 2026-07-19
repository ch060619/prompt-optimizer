# RC-191 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-190
- 目标：实现可暂停、可恢复、可校验、可重试且不会把不完整文件标记为可用的本地模型下载器。

## 实现范围

- `LocalInstallCore` 持久化 `.part` 下载、版本、镜像、代理、重试次数和指数退避状态；下载完成后才进入校验阶段，SHA-256 通过后才允许原子安装。
- 失败下载可以恢复；同一安装根目录在进程内拒绝并发写入，避免两个下载步骤同时追加同一个 `.part` 文件。
- Python CLI、PowerShell/Shell 薄包装和既有结构化 JSON 事件继续共用核心状态；CLI 支持版本、镜像、代理、重试、退避参数。

## 验证

- `backend/tests/test_rc185_local_install.py` + `backend/tests/test_rc191_downloader.py`：`8 passed`。
- RC-188/RC-191/RC-192 联合专项：`14 passed`；覆盖重启续传、暂停/恢复、失败恢复、错误哈希、指数退避、取消、不完整文件和同根目录并发写入。
- RC-149 至 RC-192 相关后端回归：`172 passed, 2 skipped`；保留既有路径迁移 `DeprecationWarning`。
- 定向 Ruff、严格 Mypy、Python 编译和模型分发 denylist 检查通过；`workspace.py check` 在追踪索引更新后通过。

## 限制

- 当前测试使用本地模拟源，使用 `seek` 模拟 Range 续传；没有执行真实 HTTP 下载、真实镜像切换、真实代理请求或 Linux 实机矩阵。
- 并发保护覆盖同一 Python 进程内的共享安装根目录；跨进程下载锁和崩溃恢复不在本项实现范围内。
