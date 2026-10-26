# 首次导入本地项目 → GitHub 私有仓库

只在用户明确要求上传时执行。用户给项目路径优先直接检查，别因本机没看见路径就新建空目录；检查实际主机和可访问设备。

## 1. 调查项目

- 先读父级/项目/子目录适用的 AGENTS.md；别违反项目特有安全边界。
- 看目录结构、README、交接、最新计划。多份 vX.Y.Z 源码目录时按**语义版本**识别最新版，结合用户指定的版本确认；用户明确要新旧多个版本时，逐份独立列入，不能自动只选最新。
- 若已经有 .git 工作树，**优先普通 Git 分支工作流**，不要重新 init 或整体复制。
- 旧版源码、压缩包和运行产物默认不上传；现有历史源码路径在仓库里暂时保留，不因新的 Git 分支规则自动移动或删除。

## 2. 使用选配 Python 助手

在 Skill 根目录执行 python run.py，stdin 传 JSON：

    {"skill_action":"inspect","project_dir":"<项目绝对路径>"}

看 file_count、by_directory、suggested_docs、findings，并人工复核被排除的源码。助手主要服务“最新版快照”模式；用户要求上传多个独立版本、并列方案或特殊构建资源时，需要**手动补全隔离副本与清单**，不能把助手筛选当完整正确。

    {"skill_action":"prepare","project_dir":"<项目绝对路径>","output_dir":"<新临时目录>","include_docs":["docs/plan/最新计划.md"]}

prepare 仅复制和写 source-manifest.json，不访问 GitHub。输出目录必须原本不存在，且不得与项目目录重叠。manifest 是**本地检查报告，不上传**。

## 3. 人工安全和完整性检查

按 [security.md](security.md) 检查密钥、.env、生产数据、过期文档、历史大文件与 Go embed/前端资源。保留 go.mod/go.sum、package-lock.json、测试夹具、运行时引用的图片、部署模板及重要 Markdown；过滤 node_modules、数据库、压缩归档、日志。必要脱敏仅改**临时副本**，记录原始与副本差异，不能修改原始项目。

上传前写中文 README、AGENTS.md、.gitignore，并加上 Git 分支协作规范，避免下一版继续用版本文件夹堆源码。

## 4. 创建并上传

    gh auth status --active
    gh repo create OWNER/REPO --private --description "项目说明" --add-readme
    gh repo view OWNER/REPO --json visibility,defaultBranchRef

默认 Private；若用户明确要求 Public，先做公开内容专项审查后再用 --public。已有仓库先确认它确实属于用户与目标项目，不能因为名称相似就覆盖。

通常在**隔离副本**中完成真实 Git commit/push，remote 使用 HTTPS，不把 Token 嵌入 URL。克隆已初始化仓库或按实际仓库初始状态建立提交，拒绝 force push：

    gh repo clone OWNER/REPO <isolated-worktree>
    # 将经审查的源码复制到工作树，逐项比对
    git status --short
    git add -- <file paths>
    git commit -m "chore: import reviewed source"
    git push -u origin HEAD

如果 git HTTPS 不通但 gh API 可达，使用 [Git Data API 后备方式](git-api.md) 真实创建 Tree/Commit/Ref。不能把单纯本地 commit 报告为远端上传完成。

## 5. 必须远端验收

- GitHub API 读回仓库 visibility/默认分支/权限及 HEAD。
- 递归读 Git Tree 并确认 truncated=false，核对目标文件数量与路径。
- 核对样本：入口文件、依赖锁、README/AGENTS、关键测试/静态资源、最新计划。
- 检查无密钥、数据库、构建缓存意外进入提交。清理**仅本轮新建**的临时目录。
- 汇报：仓库 URL、实际 Private/Public、Commit SHA、文件数量、排除项、未执行的测试/部署；不冒称完成上线。
