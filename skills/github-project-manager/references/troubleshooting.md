# GitHub/多智能体开发故障速查

## 认证与网络

- 先 gh auth status --active 与 gh api user --jq .login，看是否处于预期 GitHub 账户。不要打印 gh auth token。
- SSH Permission denied (publickey)：检查 git remote -v。可以改用 HTTPS 仓库 URL，执行 gh config set git_protocol https --host github.com 与 gh auth setup-git --hostname github.com。
- gh API 可访问但 git HTTPS:443 失败：先用 gh api 只读确定当前远端 HEAD；对于小型文件改动，改用 GitHub API/连接器提交。首次大量导入可参照 [Git Data API](git-api.md)，但必须回读真实远端提交。
- HTTP 401：检查现有认证。403：核查实际仓库写权限、组织策略或分支保护，不把仓库改 Public 绕过。404：确认仓库名及是否有读取权限；API 404 也可能是权限问题。

## PR/推送冲突

- push non-fast-forward：git fetch origin，检查双方提交：git log --oneline --graph --all -25。不能 force push 擦掉别人提交。
- 工作区未提交：先 git status --short、git diff，不执行 git reset --hard 或 git clean -fdx；按任务保存已有修改。
- 个人尚未共享的模块分支可视情况 rebase；共享分支通常 merge。出现冲突时理解双方业务后逐文件整合，不直接机械选择 ours/theirs。
- git rebase --abort / git merge --abort 只在相应未完成操作中使用。

## 多智能体认领冲突

- 同一 M01 只有一个 git ref 名称；GitHub POST /git/refs 已存在 409/422 就退出该认领，不使用 upsert、强推、先删除再建。
- 创建分支后 GitHub 计划更新失败：认领占位仍有效，工作者**暂不编码**。先最新 SHA 读回计划再登记，或请协调者核对释放。
- 多个代理同时修改计划得到 409/422：分别读取最新内容，只修改自身模块行、追加自己的日志；不以旧文档覆盖整个文件。
- 模块已完成但未有目标为 release 的 PR 或远端计划尚无“完成待集成”标记，不可宣布集成者可开始合并。
- 计划共享文件边界重叠，交给单一集成者或依赖串行；不得同时写一个入口文件。跨模块测试需要集成时须真实注明“待集成后验收”。

## 凭据风险

- 误传真实密钥：不要在聊天输出密钥或在回滚中再次暴露，及时轮换，评估 Git 历史清理。私有仓库也不例外。
- 任何真实测试、部署或涉及资金的动作应遵循项目自身业务要求，不因 GitHub 上传或 PR 合并被视为自动授权。
