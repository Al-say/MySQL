# MySQL练习系统

这是一个用于练习和评估MySQL查询的系统。该系统允许用户编写SQL查询并获得即时反馈，帮助用户提高SQL编写能力。

## 功能特点

- 实时SQL查询执行和结果展示
- 自动评分系统
- 多样化的练习题目
- 详细的错误提示
- 性能分析
- 用户进度跟踪

## 快速开始

### 前置要求

- Python 3.8+
- MySQL 5.7+
- pip

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/Al-say/MySQL.git
cd MySQL
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置数据库
```bash
mysql -u root -p < setup.sql
```

4. 运行应用
```bash
python run.py
```

访问 http://localhost:5000 开始使用

## 使用说明

1. 注册/登录账号
2. 选择练习题目
3. 在编辑器中编写SQL查询
4. 点击运行按钮执行查询
5. 查看结果和评分
6. 根据反馈修改优化

## 项目结构

```
MySQL/
├── src/                # 源代码
│   ├── models/        # 数据模型
│   ├── services/      # 业务逻辑
│   └── utils/         # 工具函数
├── tests/             # 测试文件
├── static/            # 静态资源
├── templates/         # 页面模板
├── setup.sql          # 数据库初始化脚本
├── requirements.txt   # 项目依赖
└── run.py            # 启动脚本
```

## 配置说明

主要配置项在 `config.py` 文件中：

- 数据库连接信息
- 服务器配置
- 日志设置
- 评分参数

## 开发指南

请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目开发。

## 测试

运行所有测试：
```bash
python -m pytest tests/
```

## 常见问题

1. 数据库连接失败
   - 检查MySQL服务是否运行
   - 验证连接信息是否正确

2. 依赖安装问题
   - 确保使用正确的Python版本
   - 尝试更新pip

## 更新日志

### v1.0.0
- 初始版本发布
- 基本查询功能
- 评分系统

## 贡献者

- [Al-say](https://github.com/Al-say)

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者：Al-say
- 邮箱：2678448813@qq.com
- GitHub：[https://github.com/Al-say](https://github.com/Al-say)

## 致谢

感谢所有为这个项目做出贡献的开发者。
