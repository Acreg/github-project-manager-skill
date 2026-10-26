# GitHub Project Manager Skill

一个可移植的 Agent Skill：**整理本地源码 → 上传并维护 GitHub 仓库 → 云端审查 → 分支/PR/Tag → 多智能体模块认领并行开发**。

只有 **一个** Skill：`github-project-manager`。主 `SKILL.md` 保持简洁，复杂操作按需读取相对路径下的参考文档。

## 功能

- **首次整理项目：** 检查 README/AGENTS、识别最新语义版本、筛选必要源码、扫描秘密风险、准备隔离上传副本，确认后创建 GitHub 私有仓库并远端核验。
- **日常维护：** 通过 GitHub CLI、Git 或已授权的 GitHub MCP 直接读写代码、审查 PR、Commit/Push/Tag；只读云端查看无需 clone。
- **多智能体并行：** `release/vX.Y.Z` 统一计划，`feat/vX.Y.Z/Mxx` 原子占位，**先领取并远端登记，再开始编码**；模块完成更新状态并停止，唯一集成人统一合并。
- **版本管理：** 以后通过 Git 分支和 Tag 管理新版本，不复制整份源码目录。已存在的历史目录暂时保留。
- **安全：** 私人业务项目默认 Private；此公开仓库只包含通用的 Skill、辅助脚本和安装工具。

> 这个项目是供智能体调用的协作规范与辅助脚本，不是自动上传所有文件的无人值守服务。实际 GitHub 写入需用户授权的 Git/gh/MCP。

## 内容

```text
skills/github-project-manager/
  SKILL.md                 # 约 60 行快速入口
  run.py                   # inspect / prepare / status
  references/
    import.md              # 本地项目首次整理、GitHub 上传
    security.md            # 源码筛选与密钥检查
    git.md                 # 云端直读、Git/gh/PR/Tag
    modules.md             # 模块原子认领与统一集成
    plan-template.md       # Release 计划模板
    git-api.md             # Git Data API 后备上传
    troubleshooting.md     # 认证、冲突和网络排障
  tests/test_run.py
install.ps1                # Windows 一键安装：Codex + DSH
install.sh                 # Linux/macOS 安装
```

## 一键安装

需要 Git；如使用 `inspect/prepare`，需要 Python 3.9+。实际访问 GitHub 时需要现有已授权的 `gh` / GitHub MCP。安装 Skill 本身不需要 Token。

### Windows（Codex + DSH Desktop）

```powershell
git clone https://github.com/Acreg/github-project-manager-skill.git
cd github-project-manager-skill
.\install.ps1
```

已经装过两个旧 Skill `github-cli-workflow`、`private-github-source-sync` 时：

```powershell
.\install.ps1 -ArchiveLegacy
```

它会把旧 Skill 移到用户目录的带时间戳备份文件夹，不会删除它们。默认安装到：

- Codex：`~/.agents/skills/github-project-manager`
- DSH Desktop：`~/.dsh/skills/github-project-manager`
- Claude Code 可选：`.\install.ps1 -IncludeClaude`

AgentDock 可以导入 `skills/github-project-manager/` 目录并激活，安装器不改 AgentDock 主程序或凭据。

### Linux/macOS

```sh
git clone https://github.com/Acreg/github-project-manager-skill.git
cd github-project-manager-skill
sh ./install.sh
```

## 可以这样对智能体提需求

- 「使用 github-project-manager，把指定本地项目检查并整理成 GitHub 私人仓库，保留源码和必要 Markdown。」
- 「直接在 GitHub 云端审查 OWNER/REPO，列出问题，不用克隆、不修改。」
- 「规划 v0.1.16，按互不重叠的模块拆分，认领时立即标记，完成即停止，最后由唯一集成人合并。」
- 「将已完成模块 PR 合入 release，整体真实验收后再合入 main；正式发布时打 Tag。」

## 测试

```sh
python -m unittest discover -s skills/github-project-manager/tests -v
```

这个 Skill 无必填环境变量，不会自动获取其他账号的私人仓库权限。真实构建/运行测试需要可执行的工作环境。不要把 GitHub PR 合并当作生产已经发布。

## 许可证

MIT License。
