# RC-031 执行证据

- RC ID: RC-031
- 状态：已提交（含待确认项）
- 负责人：Codex
- 基线 Commit：`8e5ab1f`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-030（M0 待批准但默认禁止规则已生效）
- 修改文件：本地模型/运行器许可证 manifest、政策、校验器和 CI 步骤
- 用户可见行为：模型安装前必须显示来源/许可/条款并确认；权重默认不进入安装包。
- 风险与假设：本轮不下载权重、不接受 gated 条款；HF API 文件哈希是固定版本元数据，不替代下载后本地 SHA 校验。

## 交付

- Ollama `03d61e19255158fc90552537aaec843b3867c2e1` 和 llama.cpp `e8f19cc0ad70a243c8012bf17b4be601abfc8ea2` 固定为 MIT runner 资料。
- Gemma `google/gemma-3-1b-it` 固定 SHA `dcc83ea841ab6100d6b47a070329e1ba4cf78752`，标为 `gemma`、manual gated、用户确认、默认禁止打包。
- Qwen `Qwen/Qwen2.5-Coder-1.5B-Instruct` 固定 SHA `2e1fd397ee46e1388853d2af2c993145b0f1098a`，标为 Apache-2.0、非 gated、按需下载、默认禁止打包。
- 记录模型文件的 HF API SHA-256/大小元数据，安装流程必须下载后重新校验。

## 验证

| 查询或命令 | 结果 | 证据路径 |
| --- | --- | --- |
| Ollama/llama.cpp GitHub API + fixed LICENSE | PASS：仓库/commit/许可证元数据与 LICENSE 页面可访问 | `docs/research/local-model-license-manifest.yml` |
| HF Gemma API | PENDING CONFIRMATION：metadata 200、license `gemma`、gated `manual`；固定 commit 页面 401 | `docs/research/local-model-license-manifest.yml` |
| HF Qwen API + LICENSE | PASS：metadata 200、Apache-2.0、非 gated、固定 commit/LICENSE 200 | `docs/research/local-model-license-manifest.yml` |
| HF file metadata API | PASS：保存模型文件 SHA-256/大小；未下载权重 | `docs/research/local-model-license-manifest.yml` |
| `python scripts/check_local_model_license_manifest.py` | PASS：2 runners、2 models、weights not downloaded | `scripts/check_local_model_license_manifest.py` |
| `python -m ruff check scripts/check_local_model_license_manifest.py` | PASS：All checks passed | `scripts/check_local_model_license_manifest.py` |

## 未解决项

- Gemma gated 模型卡正文和条款确认待用户/合规确认；在确认前保持 blocked，不下载或打包。
- Runner 完整第三方组件/NOTICE 清单留给 RC-032。

## 回滚

- 需要回滚的本项文件/迁移：删除 manifest、政策、校验器、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
