# GitHub CLI：远端优先的日常开发

## 身份与权限

    git --version
    gh --version
    gh auth status --active
    gh api user --jq '.login'
    gh repo list OWNER --limit 100 --json nameWithOwner,isPrivate,url
    gh repo view OWNER/REPO --json visibility,defaultBranchRef,url

已登录不重复授权。若 Git 认证失败但 gh 登录存在，可运行：

    gh config set git_protocol https --host github.com
    gh auth setup-git --hostname github.com

## 无需 clone：直接在云端看代码与 PR

    gh api repos/OWNER/REPO/contents
    gh api repos/OWNER/REPO/contents/README.md -H "Accept: application/vnd.github.raw"
    gh pr list -R OWNER/REPO
    gh pr view 123 -R OWNER/REPO
    gh pr diff 123 -R OWNER/REPO
    gh api repos/OWNER/REPO/git/ref/heads/main --jq .object.sha

GitHub API/MCP 可做小文件更新、审查和 PR；全局索引搜索可能延迟或受权限限制，不把搜索无结果直接当文件不存在。真正编译/运行测试需要具备执行能力的工作区，本地/云端均可。

## 需要编译或大规模开发：按需检出

    gh repo clone OWNER/REPO
    cd REPO
    git remote -v
    git status -sb
    git fetch origin --prune
    git pull --ff-only

若工作区已有未提交修改，不强拉、不丢失别人工作。多智能体并行优先不同 git worktree（独立磁盘工作树），不是将完整版本副本加入 Git：

    git worktree add -b feat/agent-m01 ../repo-m01 origin/main

## 单模块开发、Commit、PR

按项目 AGENTS.md 及其 Git 工作流选择 base 分支，通常 main；若是多人新版本，则模块 PR 目标是 release/vX.Y.Z，参见 [modules.md](modules.md)。

    git fetch origin
    git switch -c fix/example origin/main
    # 只修改分配的文件，执行本次任务相关的测试
    git status --short
    git diff --check
    git add -- path/to/file
    git diff --cached --check
    git commit -m "fix: resolve actual issue"
    git push -u origin HEAD
    gh pr create --base main --head fix/example --fill

PR 需真实审查和核对测试。普通 GitHub 协作允许以 PR 审查后合并，是否需要正式审查人遵守真实仓库规则，不人为增加审批门禁。合并后检查 main SHA。单纯提交 PR 不算合并、不算部署。

## 正式 Tag 和收尾

- 只有正式业务发布且验收确认完成，才在对应发布 Commit 打 annotated tag：git tag -a vX.Y.Z -m "Release vX.Y.Z"; git push origin vX.Y.Z。
- 合并且无剩余工作后才删除短期分支，保留 main/PR/Commit/Tag 历史。
- 遇到 403、认证失败、PR 冲突、非快进与 API 失败看 [troubleshooting.md](troubleshooting.md)。
