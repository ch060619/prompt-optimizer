# RC-048 FastAPI API 兼容契约

- RC ID: RC-048
- 状态：已完成
- 兼容窗口：V2 现有客户端继续可用；新客户端从 `/api/v1` 开始
- 规范文件：`docs/api/openapi-v1.json`
- 生成命令：`python scripts/generate_openapi.py`

## 决策

现有 `/api/*` 路径作为兼容入口保留，现有客户端不需要修改即可继续调用。新客户端必须使用相同业务实现对应的 `/api/v1/*` 版本化入口，并以导出的 OpenAPI 为请求、响应和错误契约来源。两组入口共享服务层、Pydantic Schema、认证和 SSE 实现，因此不会产生两套行为。

RC-048 不删除、重命名或静默改变旧接口；后续若要废弃 `/api/*`，必须在新的 RC 中给出迁移周期、公告和旧客户端测试结果。

## 接口矩阵

| 能力 | 旧客户端入口 | 新客户端入口 | 处置 | 兼容说明 |
| --- | --- | --- | --- | --- |
| analyze | `POST /api/analyze` | `POST /api/v1/analyze` | 保留 + 版本化 | 请求 `AnalyzeRequest`，响应 `PromptAnalysis` |
| optimize | `POST /api/optimize` | `POST /api/v1/optimize` | 保留 + 版本化 | 离线默认优化；认证用户保存版本 |
| stream | `POST /api/optimize/stream` | `POST /api/v1/optimize/stream` | 保留 + 版本化 | `text/event-stream` 事件顺序和数据结构不变 |
| task | `POST /api/tasks/*`、`GET /api/tasks/{task_id}*` | `POST /api/v1/tasks/*`、`GET /api/v1/tasks/{task_id}*` | 保留 + 版本化 | 创建返回 `TaskCreateResponse`，结果未完成时返回 409 |
| auth | `/api/auth/*` | `/api/v1/auth/*` | 保留 + 版本化 | Bearer Token、401 鉴权错误和 `AuthResponse` 不变 |
| project | `GET /api/projects` | `GET /api/v1/projects` | 保留 + 版本化 | 需要认证，按用户返回项目空间 |
| version | `/api/history*` | `/api/v1/history*` | 保留 + 版本化 | 历史、单版本和 diff 均按用户隔离 |
| template/export | `/api/templates*`、`POST /api/export` | `/api/v1/templates*`、`POST /api/v1/export` | 保留 + 版本化 | 当前客户端能力同步纳入版本化 Schema |

## 统一契约规则

- 请求体由 FastAPI OpenAPI Schema 生成；缺少必填字段或枚举值非法时返回 422。
- 受保护资源缺失或 Bearer Token 无效时返回 401；跨用户资源和不存在资源返回 404。
- 任务结果尚未成功时返回 409；SSE 错误通过 `event: error` 返回，不伪装成成功结果。
- 规范文件由脚本从 `app.openapi()` 生成并使用稳定 JSON 排序；禁止手工编辑。
- `x-api-version: v1`、`x-legacy-prefix: /api` 和 `x-rc-reference: RC IDs: RC-048` 记录版本与追踪边界。

## 验收与迁移

`backend/tests/test_api_contract.py` 覆盖 OpenAPI 路径/schema、两组 analyze 入口、v1 的 optimize/stream/task/auth/project/version，以及兼容期的鉴权和校验错误。既有 `backend/tests/test_api.py` 继续覆盖旧客户端主要工作流。

新客户端迁移时只需把 `/api` 前缀替换为 `/api/v1`，请求和响应字段无需另行适配。生成的前端客户端目录和 CI 差异门禁属于后续 RC-062；RC-048 先冻结可生成的服务端契约。
