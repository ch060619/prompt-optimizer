# RC-024 执行证据

- RC ID: RC-024
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`b252756`
- 完成 Commit：`ad7e81d`
- 前置 RC：RC-023（已完成并有证据）
- 修改文件：专有内容政策、Provenance 模板、PR 模板、CI 和校验器
- 用户可见行为：相关 PR 必须声明来源、许可证/NOTICE、原创性、字符串扫描、人工相似性审查和后续限制。
- 风险与假设：自动零命中只能说明当前检查范围没有命中，不构成法律意见或通用相似度证明。

## 交付

- 禁止清单覆盖核心源码/二进制、System Prompt、内部文案、测试、资源、私有常量、未公开端点、source-map 还原内容和机械改写。
- `docs/templates/provenance-template.md` 和 `.github/pull_request_template.md` 固定每个相关 PR 的来源证明字段。
- 产品输入检查器扫描当前代码、脚本、CI 和 Docker 入口；研究证据/审计脚本不混入产品扫描。
- CI 在 source-map denylist 后执行专有内容政策检查。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_proprietary_content_policy.py` | PASS：62 个产品输入，zero forbidden literal hits | `scripts/check_proprietary_content_policy.py` |
| `python scripts/check_source_map_denylist.py` | PASS：128 个供应链输入，zero hits | `scripts/check_source_map_denylist.py` |
| `python -m ruff check scripts/check_proprietary_content_policy.py` | PASS：All checks passed | `scripts/check_proprietary_content_policy.py` |
| 当前 RC-024 diff 人工审查 | PASS：仅政策、模板、配置和校验器；未新增外部实现、Prompt、测试夹具、资产或私有常量 | `docs/research/proprietary-content-policy.md` |
| 相似性审查 | PASS：对当前 diff 做人工范围审查；不宣称自动法律清除 | 本证据与 PR Provenance 模板 |

## 未解决项

- 后续相关 PR 仍需逐项填写 Provenance，并在发布前扫描最终制品、SBOM 和 Docker 层。
- 自动字符串零命中不替代人工相似性、许可证和法律审查。

## 回滚

- 需要回滚的本项文件/迁移：删除政策、模板、CI 步骤、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
