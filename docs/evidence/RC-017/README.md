# RC-017 执行证据

- RC ID: RC-017
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`583848a`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-016（按用户指示关闭并已记录）
- 修改文件：`docs/research/codex-source-register.yml`、`docs/research/codex-source-boundaries.md`、`scripts/check_codex_source_register.py`
- 用户可见行为：来源登记区分开源代码、公开文档和行为观察；桌面 GUI 不被视为可获取的完整开源源码。
- 风险与假设：官方 Codex manual 本轮已返回 HTTP 200；只按公开文档事实使用，不将其扩展为桌面 GUI 源码或专有资产授权。

## 交付

- `open-source` 固定到 `openai/codex` 的 SHA `78ba047bdae3db0342dee11d8d9ef5582fe8ce49`，只允许经过许可证和 NOTICE 审核的复用。
- `public-doc` 区分可访问的固定 SHA README 与当前 HTTP 403 的官方 manual；403 条目禁止形成结论。
- `behavior-only` 明确桌面 GUI 只能记录公开行为和自制观察说明，不保存专有源码、品牌资产或截图二进制。
- 校验器强制三类来源同时存在，并阻止行为来源声明不可验证的源码 URL。

## 外部核对

| 查询或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| GitHub API `repos/openai/codex` | PASS：仓库为 `openai/codex`，许可证元数据为 Apache-2.0，未归档、未禁用 | `docs/research/source-baselines.yml` |
| GitHub API 固定提交树 | PASS：SHA `78ba047bdae3db0342dee11d8d9ef5582fe8ce49` 可解析，未截断 | `docs/research/codex-source-register.yml` |
| 固定 SHA GitHub 仓库页与 README HEAD 请求 | PASS：HTTP 200 | `docs/research/codex-source-register.yml` |
| `https://developers.openai.com/codex/` HEAD 与 GET 请求 | PASS：均返回 HTTP 200；GET 返回 316872 bytes | `docs/research/codex-source-register.yml` |

## 验证

| 命令 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_codex_source_register.py` | PASS：Validated 4 Codex source entries captured on 2026-07-17 | `docs/research/codex-source-register.yml` |
| `python -m ruff check scripts/check_codex_source_register.py` | PASS：All checks passed | `scripts/check_codex_source_register.py` |
| `git grep` 代码与资源审计 | PASS：本轮未新增 Codex GUI 源码、品牌资产或截图二进制 | 本证据与 `docs/research/codex-source-boundaries.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-017 的来源登记、边界说明、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。

## 未解决项

- 无。官方 Codex manual 已恢复 HTTP 200；仍只按 `public-doc` 的事实边界使用。
