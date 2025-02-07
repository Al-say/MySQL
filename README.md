# MySQL 练习系统

基于 Python 和 PyQt6 开发的 MySQL 练习系统，集成 DeepSeek API 提供智能评分和推荐。

## 主要功能

- **题型支持：** 选择题、判断题、填空题、简答题、设计题
- **智能功能：** AI 评分、个性化推荐、知识点分析
- **实时反馈：** 即时验证、详细解析、统计分析
- **现代界面：** 响应式设计、夜间模式、快捷键支持

## 快速开始

### 环境要求
- Python 3.8+
- MySQL 8.0+
- PyQt6

### 安装步骤
```bash
git clone https://github.com/yourusername/mysql-practice-system.git
cd mysql-practice-system

python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

pip install -r requirements.txt

# 配置数据库和环境变量
cp .env.example .env
vim .env

# 初始化数据库
mysql -u root -p < database/setup.sql
python src/scripts/insert_test_questions.py
```

### 运行系统
```bash
python run.py
```

## 项目结构

```
mysql-practice-system/
├── src/
│   ├── config/          # 配置文件
│   ├── core/            # 核心逻辑
│   ├── services/        # 业务逻辑
│   ├── ui/              # 用户界面
│   └── utils/           # 工具函数
├── tests/               # 测试文件
└── database/            # 数据库相关
```

## 快捷键

- Ctrl+Enter：提交答案
- ←/→：上一题/下一题
- Ctrl+T：切换主题

## 开发相关

### 测试
```bash
python -m pytest tests/
python -m pytest tests/ --cov=src
```

### Docker 部署
```bash
# 开发环境
docker-compose -f docker/docker-compose.dev.yml up

# 生产环境
docker-compose -f docker/docker-compose.prod.yml up -d
```

## 许可证

[MIT License](LICENSE)

## 联系方式

- 作者：Alsay （me@alsay.net）
- 项目地址：[GitHub Repository](https://github.com/yourusername/mysql-practice-system)
