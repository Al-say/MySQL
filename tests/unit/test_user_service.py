"""
用户服务的单元测试
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List
from src.services.user_service import UserService
from src.database.db_manager import DatabaseManager
from src.config.constants import Constants

@pytest.fixture
def user_service(test_config):
    """创建用户服务实例"""
    db_manager = DatabaseManager(
        host=test_config['DB_HOST'],
        port=test_config['DB_PORT'],
        user=test_config['DB_USER'],
        password=test_config['DB_PASSWORD'],
        database=test_config['DB_NAME']
    )
    return UserService(db_manager)

@pytest.fixture
def mock_user_data():
    """提供模拟用户数据"""
    return {
        'user_id': 'test_user_1',
        'username': 'Test User',
        'email': 'test@example.com',
        'created_at': datetime.now(),
        'last_login': datetime.now()
    }

@pytest.fixture
def mock_answer_history():
    """提供模拟答题历史数据"""
    current_time = datetime.now()
    return [
        {
            'history_id': 1,
            'user_id': 'test_user_1',
            'question_id': 1,
            'user_answer': 'A',
            'is_correct': True,
            'answer_time': current_time - timedelta(days=1)
        },
        {
            'history_id': 2,
            'user_id': 'test_user_1',
            'question_id': 2,
            'user_answer': 'False',
            'is_correct': True,
            'answer_time': current_time
        }
    ]

class TestUserService:
    """用户服务测试类"""

    def test_get_user_basic(self, user_service, mock_user_data):
        """测试基本的用户信息获取"""
        user = user_service.get_user(mock_user_data['user_id'])
        assert user is not None
        assert isinstance(user, dict)
        
        # 验证必要字段
        required_fields = {'user_id', 'username', 'email', 'created_at', 'last_login'}
        assert all(field in user for field in required_fields)
        
        # 验证字段类型
        assert isinstance(user['user_id'], str)
        assert isinstance(user['username'], str)
        assert isinstance(user['email'], str)
        assert isinstance(user['created_at'], datetime)
        assert isinstance(user['last_login'], datetime)

    def test_get_progress_detailed(self, user_service, mock_user_data, mock_answer_history):
        """测试详细的进度获取功能"""
        progress = user_service.get_progress(mock_user_data['user_id'])
        assert isinstance(progress, dict)
        
        # 验证进度统计
        assert 'total_questions' in progress
        assert 'completed_questions' in progress
        assert 'correct_answers' in progress
        assert 'accuracy_rate' in progress
        
        # 验证数值合理性
        assert progress['total_questions'] >= progress['completed_questions']
        assert progress['completed_questions'] >= progress['correct_answers']
        assert 0 <= progress['accuracy_rate'] <= 100
        
        # 验证分类统计
        assert 'type_statistics' in progress
        assert 'difficulty_statistics' in progress
        
        # 验证趋势数据
        assert 'daily_progress' in progress
        assert isinstance(progress['daily_progress'], list)

    @pytest.mark.parametrize('time_range,expected_count', [
        ('today', 1),
        ('week', 2),
        ('month', 2),
        ('all', 2)
    ])
    def test_get_answer_history_with_time_range(self, user_service, mock_user_data, time_range, expected_count):
        """测试不同时间范围的答题历史获取"""
        history = user_service.get_answer_history(
            user_id=mock_user_data['user_id'],
            time_range=time_range
        )
        assert isinstance(history, list)
        assert len(history) == expected_count

    def test_get_answer_history_with_filters(self, user_service, mock_user_data):
        """测试带过滤条件的答题历史获取"""
        # 测试正确答案过滤
        correct_answers = user_service.get_answer_history(
            user_id=mock_user_data['user_id'],
            is_correct=True
        )
        assert all(answer['is_correct'] for answer in correct_answers)
        
        # 测试题目类型过滤
        mc_answers = user_service.get_answer_history(
            user_id=mock_user_data['user_id'],
            question_type=Constants.QUESTION_TYPES['multiple_choice']
        )
        assert all(answer['question_type'] == Constants.QUESTION_TYPES['multiple_choice'] 
                  for answer in mc_answers)

    def test_get_user_statistics(self, user_service, mock_user_data):
        """测试用户统计信息获取"""
        stats = user_service.get_user_statistics(mock_user_data['user_id'])
        assert isinstance(stats, dict)
        
        # 验证统计指标
        assert 'total_time_spent' in stats
        assert 'average_response_time' in stats
        assert 'completion_rate' in stats
        assert 'mastery_level' in stats
        
        # 验证数值范围
        assert stats['completion_rate'] >= 0
        assert stats['completion_rate'] <= 100
        assert stats['average_response_time'] > 0
        assert isinstance(stats['mastery_level'], str)

    def test_get_learning_path(self, user_service, mock_user_data):
        """测试学习路径获取"""
        path = user_service.get_learning_path(mock_user_data['user_id'])
        assert isinstance(path, list)
        
        if path:  # 如果有推荐的学习路径
            first_item = path[0]
            assert 'topic' in first_item
            assert 'difficulty' in first_item
            assert 'estimated_time' in first_item
            assert 'prerequisites' in first_item

    def test_update_user_progress(self, user_service, mock_user_data):
        """测试进度更新功能"""
        update_data = {
            'question_id': 3,
            'is_correct': True,
            'time_spent': 45,  # 秒
            'difficulty_level': Constants.DIFFICULTY_LEVELS['beginner']
        }
        
        result = user_service.update_progress(
            user_id=mock_user_data['user_id'],
            **update_data
        )
        
        assert result['success'] is True
        assert result['updated_at'] is not None
        assert isinstance(result['updated_at'], datetime)

    def test_error_handling(self, user_service):
        """测试错误处理"""
        # 测试无效的用户ID
        with pytest.raises(ValueError):
            user_service.get_progress('')
        
        # 测试无效的时间范围
        with pytest.raises(ValueError):
            user_service.get_answer_history('test_user', time_range='invalid')
        
        # 测试无效的过滤条件
        with pytest.raises(ValueError):
            user_service.get_answer_history('test_user', question_type=999)

    @pytest.mark.asyncio
    async def test_async_operations(self, user_service, mock_user_data):
        """测试异步操作"""
        # 测试异步获取进度
        progress = await user_service.get_progress_async(mock_user_data['user_id'])
        assert isinstance(progress, dict)
        
        # 测试异步获取历史
        history = await user_service.get_answer_history_async(mock_user_data['user_id'])
        assert isinstance(history, list)

    def test_user_cache(self, user_service, mock_user_data):
        """测试用户数据缓存"""
        # 第一次调用
        start_time = datetime.now()
        progress1 = user_service.get_progress(mock_user_data['user_id'])
        first_call_time = datetime.now() - start_time
        
        # 第二次调用（应该使用缓存）
        start_time = datetime.now()
        progress2 = user_service.get_progress(mock_user_data['user_id'])
        second_call_time = datetime.now() - start_time
        
        # 验证缓存生效
        assert second_call_time < first_call_time
        assert progress1 == progress2

    def test_concurrent_updates(self, user_service, mock_user_data):
        """测试并发更新处理"""
        import threading
        
        def update_progress():
            user_service.update_progress(
                user_id=mock_user_data['user_id'],
                question_id=1,
                is_correct=True,
                time_spent=30
            )
        
        # 创建多个线程同时更新
        threads = [threading.Thread(target=update_progress) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 验证最终状态
        progress = user_service.get_progress(mock_user_data['user_id'])
        assert isinstance(progress, dict)
        assert progress['completed_questions'] >= 5 