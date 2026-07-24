# Rabbit Code v3.0.0 发布指南

## 构建验证结果（2026-07-22）

| 组件 | 状态 | 产物 |
| --- | --- | --- |
| 前端 (npm run build) | PASS | `frontend/dist/` (CSS + JS) |
| Python wheel (python -m build) | PASS | `rabbit_code-3.0.0-py3-none-any.whl` |
| Tauri 桌面端 (cargo check) | PASS | 编译通过，无错误 |

## 发布步骤

### 第 1 步：提交所有变更并推送到 GitHub

```powershell
cd C:\Users\10735\Desktop\陈辉\work\github——works\prompt-optimizer

# 查看未提交的变更
git status

# 添加所有文件
git add -A

# 提交
git commit -m "feat: complete RC-280 through RC-310 — license, governance, release engineering"

# 推送到 main
git push origin main
```

### 第 2 步：在 GitHub 仓库设置中配置

打开 https://github.com/ch060619/prompt-optimizer/settings

#### 2a. About 区域（页面右上角齿轮）
- Description: `Offline-first prompt engineering toolkit with CLI, Web, and Desktop`
- Website: (留空)
- Topics: `prompt-engineering`, `llm`, `cli`, `desktop-app`, `tauri`, `offline-first`, `developer-tools`, `open-source`, `mit-license`, `python`, `react`, `typescript`

#### 2b. Branches → Add branch protection rule (main 分支)
- ☑ Require a pull request before merging
- ☑ Require status checks to pass before merging
- ☐ Do NOT require signed commits（项目政策不要求签名）
- ☑ Require conversation resolution

#### 2c. Code security
- ☐ Dependency graph (可选)
- ☑ Dependabot security updates

### 第 3 步：push v3.0.0 tag 触发自动发布

```powershell
# 创建标签
git tag -a v3.0.0 -m "Rabbit Code v3.0.0 — First stable release"

# 推送标签（这会自动触发 release.yml 工作流）
git push origin v3.0.0
```

推送标签后，GitHub Actions 会自动：
1. 构建 Python wheel
2. 构建 Tauri 桌面安装包（Windows .exe/.msi）
3. 生成 SBOM
4. 生成校验和
5. 创建 GitHub Release

### 第 4 步（可选）：发布到 PyPI（免费）

PyPI 对开源项目完全免费。步骤：

1. 注册账号：https://pypi.org/account/register/
2. 获取 API Token：https://pypi.org/manage/account/token/
3. 配置 GitHub Secret：
   - 仓库 Settings → Secrets and variables → Actions
   - 新建 secret: `PYPI_API_TOKEN` = 你的 token
4. 在 release.yml 中已有 `pypi-publish` job，会在 push tag 时自动发布

发布后用户就可以：
```bash
pip install rabbit-code
rabbit --version
```

### 第 5 步（可选）：发布到 winget / scoop（免费）

```powershell
# winget（Windows 包管理器）
# 提交 PR 到 https://github.com/microsoft/winget-pkgs
# 使用 scripts/install/winget.yml 作为模板

# scoop（Windows 包管理器）
# 提交到 https://github.com/ScoopInstaller/Extras
# 使用 scripts/install/scoop.json 作为模板
```

## 费用总结

| 渠道 | 费用 |
| --- | --- |
| GitHub 仓库 + Release | 免费 |
| GitHub Actions CI/CD | 免费（公开仓库） |
| PyPI 发布 | 免费 |
| winget / scoop | 免费 |
| 域名 | 不需要 |

**完全免费发布，用户完全免费下载使用。**

## 验证清单

发布后检查：
- [ ] GitHub Release 页面有 v3.0.0
- [ ] Release 附件包含 `.whl` 文件
- [ ] Release 附件包含 Windows 安装包
- [ ] Release 附件包含 `sbom.json`
- [ ] Release 附件包含 `checksums.txt`
- [ ] `pip install rabbit-code` 可以安装
- [ ] `rabbit --version` 输出 3.0.0
