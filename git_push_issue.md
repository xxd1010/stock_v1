# Git 推送失败问题分析与解决方案

## 排查步骤

### 1. 检查网络连接

```bash
# 测试网络连接
ping github.com

# 测试Git服务器连接
git ls-remote origin
```

### 2. 检查本地 Git 状态

```bash
# 检查本地分支状态
git status

# 检查本地提交历史
git log --oneline -5
```

### 3. 检查远程仓库状态

```bash
# 查看远程仓库信息
git remote -v

# 拉取远程最新更改（不合并）
git fetch origin

# 比较本地分支与远程分支差异
git diff HEAD origin/main
```

### 4. 检查权限设置

```bash
# 检查当前Git用户配置
git config --list | grep user

# 检查SSH密钥（如果使用SSH协议）
ssh -T git@github.com
```

## 常见问题及解决方案

### 1. 网络连接问题

**症状**：无法连接到 Git 服务器，报错类似 "Could not resolve host: github.com"

**解决方案**：

- 检查网络连接，确保可以访问互联网
- 检查防火墙设置，确保 Git 使用的端口（22 或 443）未被阻止
- 尝试更换网络环境或使用代理

**命令示例**：

```bash
# 使用代理
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy https://proxy.example.com:8080
```

### 2. 权限不足

**症状**：报错 "Permission denied (publickey)" 或 "remote: Permission to user/repo.git denied to user"

**解决方案**：

- 检查 SSH 密钥是否正确配置
- 确保当前用户有推送权限
- 检查 Git 远程 URL 是否正确

**命令示例**：

```bash
# 生成新的SSH密钥
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 检查SSH代理状态
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa

# 复制SSH公钥到剪贴板
clip < ~/.ssh/id_rsa.pub
```

### 3. 远程仓库变更未同步

**症状**：报错 "Updates were rejected because the remote contains work that you do not have locally"

**解决方案**：

- 先拉取远程最新更改，解决冲突后再推送
- 可以使用 merge 或 rebase 策略

**命令示例**：

```bash
# 使用merge策略
git pull origin main --no-ff

# 使用rebase策略
git pull origin main --rebase

# 解决冲突后，继续rebase
git rebase --continue

# 推送更改
git push origin main
```

### 4. 本地未提交的更改

**症状**：有未提交的更改，影响推送

**解决方案**：

- 提交本地更改
- 或暂存更改
- 或放弃更改

**命令示例**：

```bash
# 提交本地更改
git add .
git commit -m "提交信息"

# 暂存更改
git stash
git push origin main
git stash pop

# 放弃更改
git checkout -- .
```

### 5. 分支保护规则限制

**症状**：报错 "remote: Protected branch update failed for refs/heads/main"

**解决方案**：

- 检查远程仓库的分支保护规则
- 确保满足推送条件（如通过 CI 检查、需要 PR 等）
- 或联系仓库管理员调整规则

### 6. 本地分支与远程分支名称不匹配

**症状**：报错 "error: failed to push some refs to 'git@github.com:user/repo.git'"

**解决方案**：

- 确保本地分支与远程分支名称一致
- 或设置 upstream 关联

**命令示例**：

```bash
# 设置upstream关联
git push -u origin main

# 推送本地分支到远程（指定分支名）
git push origin local_branch:remote_branch
```

### 7. Git 配置问题

**症状**：报错 "Author identity unknown"

**解决方案**：

- 配置 Git 用户信息

**命令示例**：

```bash
# 配置全局用户信息
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"

# 配置仓库级用户信息
git config user.name "Your Name"
git config user.email "your_email@example.com"
```

## 预防措施

1. **定期拉取更新**：在推送前先拉取远程最新更改

   ```bash
   git pull origin main
   ```

2. **使用分支管理**：避免直接在主分支上开发，使用特性分支

   ```bash
   git checkout -b feature-branch
   # 开发完成后
   git checkout main
   git merge feature-branch
   git push origin main
   ```

3. **提交前检查**：提交前检查文件状态和差异

   ```bash
   git status
   git diff
   ```

4. **配置 Git 别名**：简化常用命令

   ```bash
   git config --global alias.co checkout
   git config --global alias.br branch
   git config --global alias.ci commit
   git config --global alias.st status
   ```

5. **使用 Git GUI 工具**：对于复杂操作，使用 Git GUI 工具（如 SourceTree、GitKraken）可以更直观地处理

## 常见错误代码及含义

| 错误代码 | 含义       | 可能原因                           |
| -------- | ---------- | ---------------------------------- |
| 403      | 禁止访问   | 权限不足，或远程仓库设置了访问限制 |
| 404      | 未找到     | 远程仓库不存在，或 URL 错误        |
| 500      | 服务器错误 | Git 服务器内部错误，稍后重试       |
| 502      | 网关错误   | 网络问题，或 Git 服务器暂时不可用  |
| 503      | 服务不可用 | Git 服务器过载，稍后重试           |

## 高级排查命令

```bash
# 启用Git调试模式
git push origin main --verbose

# 查看Git配置的详细信息
git config --list --show-origin

# 检查Git版本
git --version

# 查看Git日志
git reflog

# 检查Git对象完整性
git fsck
```

通过以上步骤和解决方案，您应该能够排查并解决大部分 Git 推送失败的问题。如果问题仍然存在，建议查看详细的错误日志，并联系 Git 服务器管理员或仓库所有者寻求帮助。
