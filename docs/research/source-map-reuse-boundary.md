# Claude Code Source Map 证据与边界

RC IDs: RC-021

本记录只保存 5 个仓库的 GitHub API 元数据、固定提交链接、README 可见性和 README 摘要。没有克隆、读取、运行或提交任何 source-map 还原源码正文。

## 统一处理

- 所有来源默认风险为 `high`，复用状态为 `prohibited-until-legal-review`。
- GitHub API 可以返回 license、archived 和 disabled 字段，但不能证明版权许可、DMCA 状态、删除请求状态或 source-map 内容的合法性。
- `dmca_or_deletion_check: not-observed` 表示本次 API 没有该字段，不表示“没有 DMCA”或“没有删除请求”。
- README 摘要只记录作者自述的来源性质，不将“unofficial”“cleanroom”“MIT badge”或“research”解释成第三方源码授权。

## 复核表

| 仓库 | 固定状态 | 许可证元数据 | README 摘要 | 风险 | 处理 |
| --- | --- | --- | --- | --- | --- |
| `ChinaSiro/claude-code-sourcemap` | API/Commit/README 200；未归档、未禁用 | null | 非官方 npm/source-map 重建，研究用途自述 | high | 禁止复用 |
| `oboard/claude-code-rev` | API/Commit/README 200；未归档、未禁用 | null | source-map 还原，含 shim/降级实现自述 | high | 禁止复用 |
| `ghuntley/claude-code-source-code-deobfuscation` | API/Commit/README 200；已归档、未禁用 | null | cleanroom/deobfuscation 研究预览自述 | high | 禁止复用 |
| `ComeOnOliver/claude-code-analysis` | API/Commit/README 200；未归档、未禁用 | MIT | 逆向分析自述；MIT badge 不解决还原内容权利 | high | 禁止复用 |
| `dadiaomengmeimei/claude-code-sourcemap-learning-notebook` | API/Commit/README 200；未归档、未禁用 | MIT | source-map 学习/逆向分析自述；MIT 元数据不解决第三方还原内容权利 | high | 禁止复用 |

完整字段、SHA 和响应状态见 `docs/research/source-map-evidence.yml`。

## 后续复核

下一次复核必须重新查询 API、固定提交链接、README 状态、归档/禁用状态和可观察的删除/DMCA 通知。若仓库消失、变更许可证或出现权利声明，默认维持禁止复用并创建新的 ADR；不能以旧快照推断当前状态。
