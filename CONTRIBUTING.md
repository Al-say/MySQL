# 贡献指南

感谢您考虑为MySQL练习系统做出贡献！

## 如何贡献

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 开发环境设置

1. 克隆仓库
```bash
git clone https://github.com/yourusername/mysql-practice-system.git
cd mysql-practice-system
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 代码规范

- 遵循 PEP 8 编码规范
- 使用有意义的变量名和函数名
- 添加适当的注释和文档字符串
- 确保代码通过所有测试

## 提交规范

提交信息应该清晰地描述更改内容，建议使用以下格式：

- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式化
- refactor: 代码重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

示例：`feat: 添加用户认证功能`

## 测试

- 添加新功能时，请编写相应的测试用例
- 确保所有测试都能通过
- 运行测试：`python -m pytest tests/`

## 文档

- 更新 README.md
- 添加/更新 API 文档
- 添加/更新用户指南
- 添加示例代码（如果适用）

## 问题反馈

- 使用 GitHub Issues 提交问题
- 清晰描述问题和复现步骤
- 提供相关的日志和错误信息
- 标注问题的优先级和类型

## 功能请求

- 使用 GitHub Issues 提交功能请求
- 描述新功能的用途和价值
- 提供可能的实现方案
- 考虑向后兼容性

## 行为准则

- 尊重所有贡献者
- 保持专业和友好的交流
- 接受建设性的批评
- 关注问题本身而不是个人

## 许可证

贡献的代码将使用与项目相同的许可证。 