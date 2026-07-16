# RC-050 离线规则最终降级

- RC ID: RC-050
- 状态：已完成
- Provider ID：`offline`
- UI 名称：离线规则

## Provider 边界

`OfflineRuleProvider` 是进程内规则优化后端，不加载模型、不读取远程配置、不创建 HTTP 客户端，也不访问网络。`ProviderRegistry` 在初始化时始终注册它，因此没有 API Key、模型未安装或远程服务不可用时仍有本地可执行路径。

| 元数据 | 值 |
| --- | --- |
| `name` | `offline` |
| `display_name` | `离线规则` |
| `is_model` | `false` |
| `network_access` | `false` |
| `fallback_triggers` | `provider_error`、`provider_timeout`、`provider_rate_limit`、`provider_unavailable` |

## 降级契约

`AppServices.optimize_and_save` 和流式优化在远程 Provider 抛出上述错误时调用 `offline`。成功响应保留现有元数据字段：

- `provider_requested` 保留用户选择的远程 Provider；
- `provider_used` 为 `offline`；
- `fallback_used` 为 `true`；
- `error_summary` 为原始失败原因。

因此同步响应和 SSE `fallback` 事件都能明确表示“已降级”和“为什么降级”。用户直接选择离线规则时，`fallback_used` 为 `false`，表示这是主动的本地路线而不是故障回退。

工作台把 `provider_used=offline` 显示为“离线规则”，不把规则后端标成模型；发生回退时同时显示降级原因。网络失败、超时、限流和远程 Provider 配置不可用的行为由 `backend/tests/test_offline_fallback_contract.py` 固定。

## 非目标与后续

本项不安装或下载本地模型，不改变远程 Provider 协议，不增加新的持久化状态。Provider Protocol 和多 Provider Adapter 拆分由 RC-049 负责；本地模型安装与运行器由后续 RC 负责。
