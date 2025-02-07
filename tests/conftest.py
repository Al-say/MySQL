"""
Pytest配置文件
定义测试所需的fixture和配置
"""

import os
import pytest
from typing import Dict, Any

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    提供测试配置
    """
    return {
        "DB_HOST": "localhost",
        "DB_PORT": 3306,
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_NAME": "test_mysql_exercise_db",
        "DEEPSEEK_API_KEY": "test_api_key"
    }

@pytest.fixture(scope="session")
def test_db(test_config):
    """
    提供测试数据库连接
    """
    # 这里将来添加数据库连接逻辑
    yield
    # 清理测试数据

@pytest.fixture(scope="function")
def sample_question():
    """
    提供示例题目数据
    """
    return {
        "id": 1,
        "type_id": 1,
        "content": "显示所有数据库的SQL命令是什么？",
        "difficulty_level": 1,
        "correct_answer": "SHOW DATABASES;"
    }

@pytest.fixture(scope="function")
def sample_user():
    """
    提供示例用户数据
    """
    return {
        "id": "test_user_1",
        "name": "Test User",
        "progress": {
            "completed_questions": 0,
            "correct_answers": 0
        }
    } 