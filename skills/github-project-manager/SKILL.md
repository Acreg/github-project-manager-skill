---
name: github-project-manager
description: 当用户要把本地项目整理上传 GitHub 私人仓库、通过 GitHub CLI/API 远端读写审查源码、提交和同步 Git、创建 PR/Tag，或多个智能体拆分模块、原子认领、实时标记、统一合并新版本时使用。
version: 1.0.0
---

# GitHub 项目管家

**先判断意图，再行动；只读任务不写入。** 优先复用系统现有 `git`、`gh` 授权或 GitHub MCP，不索取、不记录 Token。GitHub 私有项目默认保持 **Private**。允许 GitHub 云端直读，无需为了审查而克隆。具体步骤按需打开下列相对文档，别把整份手册一次加载。

## 立即开工：四条路径

| 用户需求 | 最短操作 | 需要时再读 |
|---|---|---|
| **本地源码首次整理并上传** | 检查项目 AGENTS → 最新源码/文档/密钥 → 临时副本 → 创建 Private 仓库 → 推送 → 远端核验 | [首次导入](references/import.md)、[筛选与安全](references/security.md) |
| **看云端源码 / 代码审查** | `gh repo view OWNER/REPO`；`gh api repos/OWNER/REPO/contents/路径 -H "Accept: application/vnd.github.raw"`；按需 PR diff | [Git 日常命令](references/git.md) |
| **单任务开发、修复、同步** | 确认分支/工作区 → 只改任务相关文件 → Commit → Push → PR → 验证远端 | [Git 日常命令](references/git.md) |
| **新版本多人并行开发** | 建 `release/vX.Y.Z` 与唯一计划 → 原子认领模块 → 远端立即登记 → 各自 PR → 唯一集成人合并 → Tag | [模块并行](references/modules.md) |

## 开始前的 20 秒检查

```sh
git --version
gh --version
gh auth status --active
gh api user --jq .login
gh repo view OWNER/REPO --json nameWithOwner,visibility,defaultBranchRef
```

若已授权**不要重新登录**；无授权时才运行 `gh auth login --hostname github.com --git-protocol https --web`、`gh auth setup-git`。权限由当前 GitHub 身份决定。报 401/403/404、SSH/HTTPS 问题和冲突时看 [故障处理](references/troubleshooting.md)。

## 首次导入：可选只读助手

需要自动识别最高 `vX.Y.Z` 目录并做隔离复制时，在本 Skill 根目录运行 `python run.py`，stdin 传 JSON（**不执行 GitHub 写入**）：

```json
{"skill_action":"inspect","project_dir":"<绝对项目目录>"}
```

```json
{"skill_action":"prepare","project_dir":"<绝对项目目录>","output_dir":"<本轮未存在的临时目录>"}
```

审核本地 `source-manifest.json` 和风险项后，才能使用 `gh`、Git 或 GitHub MCP 真实上传。不要上传清单本身、秘密、数据库和运行数据；保留构建必需资源。已有版本目录只是旧布局，**以后新版本用 Git 分支，不再整份复制源码目录**。

## 并行任务的六条硬规则

1. 开发前先在 **release 分支** 建唯一计划：模块 ID、互不重叠的可改文件、依赖、负责人、状态、PR。
2. **先原子抢占**：GitHub `POST /git/refs` 只创建唯一 `feat/vX.Y.Z/M01`，已存在则不抢写。**马上更新 release 计划并读回，之后才编码**。
3. 计划写入使用最新文件 SHA，冲突重读再合并；仅抢占成功但登记失败属于**已占位未登记**，不得开工。
4. 只改认领模块，里程碑实时更新远端计划，禁止不同代理并写共享文件。
5. 完成后 Push + 模块 PR → release + 标记**完成待集成**，工作者**停止领取任务**。
6. 全部完成由**唯一集成人**合并测试并发起 release → main 总 PR；**真实正式发布后**才打 Tag，确认无待保存工作后删除分支。

## 交付与边界

- GitHub 写入必须来自用户明确任务；不自动部署、重启或清理生产环境，不 force push、不覆盖未经确认的已有工作。
- 报告真实仓库 URL、Private/Public、提交 SHA、PR、测试和未完成项。创建提交 ≠ 推送完成；合并 PR ≠ 正式发布。
- 这里的 `OWNER/REPO` 与 `vX.Y.Z` 均需替换；当前仓库内的 `AGENTS.md`、计划、分支保护和业务安全要求优先于示例。
- 无必填环境变量。公开发布的是 **Skill 使用说明与辅助脚本**，不能上传用户的私人仓库源码或本机认证配置。
