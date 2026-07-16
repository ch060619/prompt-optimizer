# RC-055 执行证据

- RC ID: RC-055
- 状态：执行中，待完成状态提交
- 负责人：Codex
- 基线 Commit：`319f2e4`
- 独立开发分支：`codex/rabbit-code`
- 修改范围：版本元数据、V2/Rabbit Code 版本线迁移说明

## 引用核对

| 检查 | 结果 |
| --- | --- |
| `v2.0` peeled commit | `8306d117dab0dc55b5b694738cfb0f69478118eb` |
| `v2.0-baseline` peeled commit | `8306d117dab0dc55b5b694738cfb0f69478118eb` |
| `release/v2.0` | `a4c88407fb079c16af7e812e1948028b7afcc130`，保护已启用 |
| RC-051 完成提交 | `319f2e402c79d3675d4ff5f55a977a353a5d6d68` |
| 用户未跟踪文件 | `.runtime/`、`frontend/.openapi.json` 保留，未暂存 |

## 干净 V2 重建

从 `v2.0` 归档到两个独立临时目录，使用 Python `3.12.10`、Node `v24.15.0`、npm `11.12.1`、Git `2.54.0.windows.1` 验证：

- 后端 `python -m pytest backend/tests -q`：`31 passed`。
- 前端两次 `npm ci --ignore-scripts` 和 `npm run build`：均通过。
- 两次 `python -m pip wheel --no-deps backend --wheel-dir ...`：均通过。
- Git archive SHA-256：两次均为 `3261E009A00878A1F9647044FD22E365A25EC987E73B1DBCB6DDDFD0D2601665`。
- Python wheel SHA-256：两次均为 `B8DBDDBA87C34A83195A40C71E91BC8FAFD7F7CB5DE25D57ACD938C25458E575`。
- `frontend/dist` 文件哈希树：两次均为 `5DCF81B24AA939CD87C147C89980772A30A920B5D608D9BAC54F2E4B2ED26A0E`。

## 保护结果

- `release/v2.0` 已启用 Pull Request、1 个审批、管理员强制、线性历史、会话解决、禁止强推和删除。
- Ruleset `Protect V2 release tags`（ID `19066305`）已对 `v2.0` 与 `v2.0-baseline` 启用创建、更新、删除和非快进保护。
- 现有标签 ref 在保护前后均未改变；标签签名要求留给 RC-277。

## 变更

- `backend/pyproject.toml`、`backend/src/prompt_optimizer/__init__.py`：Rabbit Code 版本 `3.0.0`。
- `frontend/package.json`、`frontend/package-lock.json`：Rabbit Code Web 版本 `3.0.0`。
- `docs/migrations/RC-055-v2-release-line.md`：记录 V2 引用、分支/版本关系、保护和复现命令。

最终状态提交会补充真实完成 Commit，并更新主控计划的 RC-055 日志和下一指针。
