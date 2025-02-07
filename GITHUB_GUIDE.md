# GitHub 项目上传指南

## 准备工作
1. 确保已安装 Git
2. 配置 Git 用户信息：
   ```
   git config --global user.name "你的GitHub用户名"
   git config --global user.email "你的邮箱"
   ```

## 上传步骤
1. 在 GitHub 网站上创建新仓库
   - 访问 https://github.com/new
   - 填写仓库名称
   - 选择公开/私有
   - 不要初始化README文件

2. 在本地项目目录中执行以下命令：
   ```
   cd /e:/BaiduSyncdisk/Python_file/Project
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/你的用户名/仓库名称.git
   git push -u origin main
   ```

## 注意事项
1. 确保 .gitignore 文件正确配置，避免上传不必要的文件
2. 如果遇到推送失败，可能需要先进行身份验证
3. 大文件建议使用 Git LFS 处理
