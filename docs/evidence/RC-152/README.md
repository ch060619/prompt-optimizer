# RC-152 执行证据

- RC ID: RC-152
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-151
- 修改文件：`backend/src/prompt_optimizer/streaming.py`、`backend/src/prompt_optimizer/api/app.py`、`backend/tests/test_rc152_stream_events.py`、`packages/protocol/rabbit_code_protocol/models.py`、`frontend/src/api.ts`、`frontend/src/App.tsx`、`frontend/src/generated/client.ts`、`scripts/generate_api.py`

## 已交付

- v1 优化 SSE 事件使用 `started`、`analysis`、`delta`、`saved`、`completed`、`cancelled`、`error` 事件，事件带 request ID、单调 `seq`、协议版本和 payload；旧 `/api` 保留 `chunk` 兼容输出。
- 优化 SSE 使用进程内 bounded event log 保存已确认事件；客户端以 `X-Request-ID` 和 `Last-Event-ID` 重连时只回放游标之后的事件，不重新调用 Provider，不重复保存版本。
- 新增取消路由，取消事件幂等并可被游标回放；Provider/服务错误写入 error 终态，前端解析 canonical envelope 并支持 delta/cancelled 状态。
- 生成客户端支持 `requestId` 和 `afterSeq`，由 `scripts/generate_api.py` 维护，避免手改生成文件漂移。

## 专项验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc152_stream_events.py backend/tests/test_api.py backend/tests/test_api_contract.py -q` | PASS：25 passed、26 warnings；覆盖事件顺序/序号、saved、重连回放、取消和 error 终态，并保持旧 `/api` chunk 兼容 | `backend/tests/test_rc152_stream_events.py` |
| `npm --prefix frontend test -- --run tests/App.test.tsx tests/PromptHistory.test.tsx` | PASS：2 test files、17 passed；覆盖 canonical/legacy stream payload 消费和既有历史流式请求 | `frontend/tests/App.test.tsx`、`frontend/tests/PromptHistory.test.tsx` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 成功 | `frontend/src/api.ts`、`frontend/src/generated/client.ts` |
| `python -m ruff check ...` | PASS：无 Ruff 问题 | RC-152 修改的后端源文件和测试 |
| `python -m mypy ...` | PASS：API、streaming 和 RC-152 测试无类型问题 | RC-152 修改的后端源文件和测试 |

## 根级验证

`python scripts/workspace.py verify`：PASS。后端 329 passed、5 skipped、44 warnings；前端 19 test files、82 passed；生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁、Ruff、Mypy、Lint 和 Vite Build 全部通过。既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 如实保留。

## 未解决项与后续

- event log 当前为单进程 bounded 内存存储；跨进程/持久化事件账本和断线期间继续执行的 worker 协调留给后续任务。
- RC-153 继续处理专用 System Prompt、版本和注入边界；RC-152 不扩展为跨进程实时重连服务。
- RC-127/RC-121/RC-057/RC-060 外部条件仍 pending；既有迁移 DeprecationWarning 和前端 jsdom navigation warning 不阻塞本项。

## 回滚

- 删除内部优化 stream log、取消路由、canonical envelope/client cursor 参数及 RC-152 测试；恢复现有 `/api`/`/api/v1` 直接 SSE 事件输出。
