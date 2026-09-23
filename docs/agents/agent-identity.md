# Agent 身份：让 agent 的提交可归属

**状态**：已落地（2026-09-23 实测通过）
**适用**：本仓（`zhengcookie/xiao-zheng-voice`）以及任何「人和 agent 共用同一台机器」的场景。

## 问题

本仓提交默认沿用 global 身份 `zhengcookie <z2132085753@outlook.com>`，人与 agent 完全不可区分：

- 按 `--author` 统计产出时，agent 的活会被算到人头上（或反过来，算不清它干了多少）。
- 合并到 master 时，squash 会把作者改写成**按下合并键的那个人**，agent 存在过的痕迹一并消失。

## 裁定口径

**身份管「标记」，权限管「合并」，两件事分开设计。**

本文件只解决「标记」这一半：不需要给 agent 新账号，也不需要动 ruleset。

## 怎么配（四步）

```powershell
$root = "D:\answer skils\xiao zheng voice"
$wt   = "$root\.tmp\wt-agent-probe"

# 1) 前提：允许多工作树各自持有配置（仓库级，只写 .git/config，一次）
git -C $root config extensions.worktreeConfig true

# 2) 隔离工作区
git -C $root worktree add -b feat/agent-probe $wt

# 3) 身份只写给这个工作树（注意 --worktree）
git -C $wt config --worktree user.name  "zhengcookie-agent"
git -C $wt config --worktree user.email "129931066+zhengcookie@users.noreply.github.com"

# 4) 不用提交就能验
git -C $wt var GIT_AUTHOR_IDENT
```

身份落在 `.git/worktrees/<name>/config.worktree` —— 主树与其它工作树都不受影响。

## 判据（六条，实测均通过）

| 判据 | 本仓实测 |
|---|---|
| 配置分层里 worktree 层存在且最后生效 | global + worktree 两层，worktree 在后 |
| `git var GIT_AUTHOR_IDENT` | `zhengcookie-agent <129931066+zhengcookie@users.noreply.github.com>` |
| 提交里的作者与提交者 | `55811d7` · A=C=`zhengcookie-agent <…@users.noreply.github.com>` |
| 按名字能筛出归属 | `git -C $wt log --author='-agent' --oneline --all` → `55811d7` |
| 主树身份未被改动 | `zhengcookie <z2132085753@outlook.com>`；`.git/config` 里无 `user.*` |
| 环境变量没有盖过配置 | 只有 `GIT_PAGER`，无 `GIT_AUTHOR_*` |

## 修正：本仓看到的是两层，不是三层

FL 仓里 `git config --list --show-origin --show-scope` 会看到 global / local / worktree **三层**（因为它的 `.git/config` 里另有一份 `user.name`）。本仓 local 层为空，只会看到 **global + worktree** 两层。

⇒ 判据应写成「**worktree 层存在且最后生效**」，不要照抄「三层」。

## 不能交给 agent 的三件

1. **账号层归属** —— noreply 邮箱与账号 ID 的对应关系（本仓 `129931066+zhengcookie@users.noreply.github.com`）需要账号持有人确认。注意本仓 global 用的是真邮箱 `z2132085753@outlook.com`，并非 noreply 形状。
2. **服务端 ruleset / 分支保护** —— 需要 admin 权限。本仓当前无 `.github`，没有任何 CI 可依赖，agent 不能凭空装一道闸门。
3. **「签收在人、合并不限人」这类口径** —— 那是裁定，不是配置。

## 两个会咬人的坑

- **环境变量压过配置**：`GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` 优先于**所有**配置文件。本仓当前进程内实测为空（只有 `GIT_PAGER`），但换 harness 或换环境必须重验。验收要两条一起看：环境变量为空 **且** `git var` 显示 agent 名。
- **不带 `--worktree` 的 `git config`** 会写进 `.git/config`，等于把 agent 身份钉进主树。

## 现场记录

- 工作树：`.tmp/wt-agent-probe`，分支 `feat/agent-probe`，基于 `6cafaf9`
- 放仓内而非仓外兄弟目录：`.tmp/` 与 `.scratch/` 均被 `.gitignore` 覆盖（零未跟踪残留），且会话沙箱为 `workspace-write`，仓外路径会被拒
- 身份文件：`.git/worktrees/wt-agent-probe/config.worktree`
- 探针提交：`55811d7 chore: agent 身份探针`（**未推送**，空提交，无文件改动）
- `extensions.worktreeConfig` 已从「未设」变为 `true`

## 撤回

```powershell
$root = "D:\answer skils\xiao zheng voice"
git -C $root worktree remove .tmp/wt-agent-probe
git -C $root branch -D feat/agent-probe
git -C $root config --unset extensions.worktreeConfig
```

## 还没做

- **派活口径**：`docs/agents/` 下尚无派活文档（issue dispatch）。
- **收口**：本仓无 `.github`，无 CI 必检、无分支保护；真正推送后还要面对 squash 改写作者的问题。
