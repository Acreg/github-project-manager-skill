# GitHub Git Data API 后备上传流程

仅在 git push 连接确实不可用、现有 GitHub 连接已授权且用户明确要求上传时使用。不把本地提交当远端成功。建议每批 Tree JSON 小于约 800 KB；所有上传以**非强制、可回滚**方式推进。

1. GET repos/OWNER/REPO → 验证仓库为期望 visibility、账号有写权限。
2. GET repos/OWNER/REPO/git/ref/heads/main → 记录旧 HEAD SHA。
3. GET repos/OWNER/REPO/git/commits/{HEAD} → 获取 base tree SHA。
4. 文本：按 UTF-8 准备 {path,mode:"100644",type:"blob",content:...}。调用 POST repos/OWNER/REPO/git/trees，传 base_tree 与数组，每次得到的 tree SHA 作为下一批 base_tree。
5. 二进制（必需图片或静态资源）：用 POST repos/OWNER/REPO/git/blobs 传 base64 内容拿 SHA，再用 {path,mode:"100644",type:"blob",sha:...} 更新 tree。
6. POST repos/OWNER/REPO/git/commits，传最终 tree SHA、message 和 parents:[旧 HEAD] 创建真实 Git Commit。
7. PATCH repos/OWNER/REPO/git/refs/heads/main，将 SHA 指到新提交，force=false。若有期望父 SHA 的宿主工具则一并传入；任何并发变更要重新核对，不直接覆盖。
8. GET 远端 HEAD、递归 Tree（要求 truncated=false），抽样 GET 关键文件并与本地哈希核对；确认真实远端同步完成才能清理临时缓存。

本例以 main 为示例，实际要从 gh repo view 读取默认分支。已有仓库应保护无关文件，不能通过新树内容误删以前的文件。错误 409/422 要重新取当前 HEAD、核对差异。HTTP 403 通常是权限/分支保护，不允许绕过。
