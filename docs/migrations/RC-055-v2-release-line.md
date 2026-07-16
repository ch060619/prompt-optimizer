# RC-055 V2 发布线与 Rabbit Code 版本线

- RC ID: RC-055
- 状态：执行中，待完成状态提交
- V2 版本：`prompt-optimizer 2.0.0`
- Rabbit Code 版本线：`3.0.x`
- Rabbit Code 开发分支：`codex/rabbit-code`

## 冻结的 V2 引用

| 引用 | 类型 | 对象/提交 | 结论 |
| --- | --- | --- | --- |
| `v2.0` | annotated tag | tag object `74a752c2780f8a721a0e2609fc0f99c0a0c0e97d`，peeled commit `8306d117dab0dc55b5b694738cfb0f69478118eb` | 保留，不移动、不删除、不重写 |
| `v2.0-baseline` | annotated tag | tag object `6e4637f46ec1a74aeb5381eff839d3904974e6da`，peeled commit `8306d117dab0dc55b5b694738cfb0f69478118eb` | 与 `v2.0` 内容基线一致，保留，不移动、不删除、不重写 |
| `release/v2.0` | branch | `a4c88407fb079c16af7e812e1948028b7afcc130` | 保护的 V2 发布分支；它不是标签的同一提交，制品源仍以标签为准 |

`release/v2.0` 与 Rabbit Code 线的共同提交为 `ab7b65b4acefdafa606c889988d26840aecec861`。因此后续 Rabbit Code 改动只进入 `codex/rabbit-code`，不会通过重写或强推改变 V2 标签或发布分支历史。

## Rabbit Code 版本关系

`codex/rabbit-code` 从完成 RC-051 的 `319f2e402c79d3675d4ff5f55a977a353a5d6d68` 建立。该分支将发行包、前端包和兼容模块版本统一到 `3.0.0`：

| 文件/标识 | V2 标签 | Rabbit Code 线 |
| --- | --- | --- |
| `backend/pyproject.toml` | `prompt-optimizer` `2.0.0` | `rabbit-code` `3.0.0` |
| `backend/src/prompt_optimizer/__init__.py` | `2.0.0` | `3.0.0` |
| `frontend/package.json` 与锁文件根包 | `prompt-optimizer-web` `2.0.0` | `rabbit-code-web` `3.0.0` |
| Python import 路径 | `prompt_optimizer` | 继续保留，作为兼容边界 |

`3.0.0` 是 RC-051/RC-054 记录的旧入口兼容截止版本；本分支的版本号与该迁移约定一致。V2 的包名、版本和历史产品标题不回写。

## 保护策略

已通过 GitHub 仓库设置完成以下保护，未改变任何 Git ref 指向：

- `release/v2.0`：必须通过 Pull Request，至少 1 个审批，强制管理员遵守保护，要求线性历史和会话解决，禁止强推与删除。
- `v2.0`、`v2.0-baseline`：Ruleset `Protect V2 release tags` 已启用，禁止创建、更新、删除和非快进改写匹配标签。
- 标签未启用签名要求；签名/来源证明属于 RC-277，不能把当前未签名标签误记为已签名发布。

## 可复现性证据

环境：Python `3.12.10`、Node `v24.15.0`、npm `11.12.1`、Git `2.54.0.windows.1`；V2 前端构建使用锁文件和 `npm ci`，后端使用 `pyproject.toml` 的 Hatchling 构建后端。

从 `v2.0` 归档到两个独立临时目录后执行：

```text
python -m pytest backend/tests -q                 -> 31 passed
npm ci --ignore-scripts                            -> 310 packages installed
npm run build                                      -> passed
python -m pip wheel --no-deps backend --wheel-dir  -> passed (twice)
```

两次构建的校验和：

| 产物 | 第一次 | 第二次 | 结果 |
| --- | --- | --- | --- |
| Git archive `v2.0` | `3261E009A00878A1F9647044FD22E365A25EC987E73B1DBCB6DDDFD0D2601665` | `3261E009A00878A1F9647044FD22E365A25EC987E73B1DBCB6DDDFD0D2601665` | MATCH |
| Python wheel `prompt_optimizer-2.0.0-py3-none-any.whl` | `B8DBDDBA87C34A83195A40C71E91BC8FAFD7F7CB5DE25D57ACD938C25458E575` | `B8DBDDBA87C34A83195A40C71E91BC8FAFD7F7CB5DE25D57ACD938C25458E575` | MATCH |
| `frontend/dist` 文件哈希树 | `5DCF81B24AA939CD87C147C89980772A30A920B5D608D9BAC54F2E4B2ED26A0E` | `5DCF81B24AA939CD87C147C89980772A30A920B5D608D9BAC54F2E4B2ED26A0E` | MATCH |

Python wheel 的第一次迁移记录曾把输出截断；当前表格和 `docs/evidence/RC-055/README.md` 均以完整校验和为准。

## 边界

本项不实现安装包签名、公证、SBOM、独立二进制分发或兼容入口删除；这些由 RC-273、RC-277、RC-279 和发布门禁处理。未跟踪的 `.runtime/` 与 `frontend/.openapi.json` 不属于本项修改范围。
