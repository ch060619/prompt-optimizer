# 第三方登记册政策

RC IDs: RC-032

- `docs/research/third-party-register.yml` 是当前直接/构建依赖和复用来源的登记入口；脚本从 backend `pyproject.toml` 和 frontend `package.json` 对账。
- 每条依赖必须有生态、名称、声明版本范围、观察版本、来源 URL、许可证状态、NOTICE 状态、分发状态、修改状态和替代方案字段。
- `reused_sources` 当前显式为空；研究来源不等于复用来源，未登记的复制代码不能进入实现 Issue、依赖、CI、SBOM 或发布物。
- `THIRD_PARTY_NOTICES.md` 由脚本生成；`pending-confirmation`/`review-required` 条目会阻止发布放行，不能被手工改成批准。
- 该登记册覆盖直接/构建依赖，不替代锁文件、传递依赖、运行器组件和发布 SBOM 的逐层审计；这些在后续发布门禁继续对账。
