# 📤 如何推送到GitHub并自动打包

## ✅ 已完成的准备工作

- ✅ Git仓库已初始化
- ✅ GitHub Actions配置已创建
- ✅ 所有代码已提交
- ✅ README.md已创建

## 🚀 接下来的步骤

### 步骤1：在GitHub创建仓库

1. 访问 https://github.com/new
2. 填写信息：
   - **Repository name**: `price-suite`（或你喜欢的名字）
   - **Description**: `智能选品铺货系统`
   - **Public** 或 **Private**（建议Private）
   - ❌ **不要**勾选 "Add a README file"
   - ❌ **不要**勾选 "Add .gitignore"
   - ❌ **不要**选择 License
3. 点击 **Create repository**

### 步骤2：推送代码到GitHub

GitHub会显示推送命令，复制执行：

```bash
# 在WSL执行
cd /home/user/projects/shopxo-master/apps/price-suite

# 添加远程仓库（替换成你的GitHub用户名）
git remote add origin https://github.com/你的用户名/price-suite.git

# 推送代码
git branch -M main
git push -u origin main
```

**如果需要登录**：
- 用户名: 你的GitHub用户名
- 密码: 使用Personal Access Token（不是GitHub密码）

#### 创建Personal Access Token:

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 **Generate new token (classic)**
3. 勾选权限：
   - ✅ `repo`（完整权限）
   - ✅ `workflow`
4. 生成后复制token（只显示一次！）
5. 推送时用token作为密码

### 步骤3：查看自动打包

推送成功后：

1. 访问你的GitHub仓库
2. 点击 **Actions** 标签
3. 会看到正在运行的工作流 "Build Windows EXE"
4. 等待3-5分钟（显示绿色✅表示成功）
5. 点击完成的工作流
6. 在 **Artifacts** 区域下载 **智能选品系统.exe**

### 步骤4：下载exe

```
GitHub仓库 → Actions → 最新运行 → Artifacts → 智能选品系统
点击下载，得到zip文件
解压后就是 智能选品系统.exe
```

## 🎉 完成！

现在每次你推送代码，GitHub都会自动打包exe！

---

## 📝 常用命令

### 更新代码并自动打包

```bash
cd /home/user/projects/shopxo-master/apps/price-suite

# 修改代码后
git add .
git commit -m "更新功能"
git push

# GitHub自动打包，去Actions下载新的exe
```

### 手动触发打包

1. GitHub仓库 → Actions
2. 选择 "Build Windows EXE"
3. 点击 "Run workflow"
4. 选择分支 → "Run workflow"

---

## ⚠️ 如果推送失败

### 错误1: 需要认证

```bash
# 使用SSH方式（推荐）
ssh-keygen -t ed25519 -C "你的邮箱"
cat ~/.ssh/id_ed25519.pub
# 复制公钥，添加到GitHub → Settings → SSH keys

# 修改远程地址为SSH
git remote set-url origin git@github.com:你的用户名/price-suite.git
git push
```

### 错误2: 权限不足

确保Personal Access Token包含 `repo` 和 `workflow` 权限

### 错误3: 分支名称问题

```bash
# 检查当前分支
git branch

# 如果是master，改为main
git branch -M main
git push -u origin main
```

---

## 💡 提示

- 每次推送都会自动打包
- Artifacts保留30天
- 可以下载历史版本的exe
- Private仓库也能用Actions（每月免费2000分钟）

有问题随时问！



